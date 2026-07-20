import {
  BadRequestException,
  ConflictException,
  Inject,
  Injectable,
  Logger,
  NotFoundException,
  OnModuleInit,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { In, Repository } from 'typeorm';
import { DatasetsService } from '../datasets/datasets.service';
import { ML_SERVICE_PORT, MlDatasetItem, MlMetrics, MlServicePort } from '../ml/ml-service.port';
import { CreateTrainingJobDto, ImportModelDto } from './dto/training.dto';
import { ModelVersionEntity } from './entities/model-version.entity';
import { TrainingJobEntity } from './entities/training-job.entity';
import { TrainingMetricEntity } from './entities/training-metric.entity';

const BETO = 'dccuchile/bert-base-spanish-wwm-cased';
const POLL_MS = 3000;
/** Fallos consecutivos de polling tolerados antes de marcar el job como failed (~30 s). */
const MAX_POLL_FAILURES = 10;

export function isModelRecommended(metrics: MlMetrics): boolean {
  const perClass = metrics.per_class ?? [];
  const beatsBaseline = metrics.baseline != null && metrics.f1_macro > metrics.baseline.f1_macro;
  return (
    beatsBaseline &&
    metrics.f1_macro >= 0.7 &&
    perClass.length > 0 &&
    perClass.every((row) => row.f1 >= 0.5)
  );
}

@Injectable()
export class TrainingService implements OnModuleInit {
  private readonly logger = new Logger(TrainingService.name);

  constructor(
    @InjectRepository(ModelVersionEntity) private readonly versions: Repository<ModelVersionEntity>,
    @InjectRepository(TrainingJobEntity) private readonly jobs: Repository<TrainingJobEntity>,
    @InjectRepository(TrainingMetricEntity) private readonly metrics: Repository<TrainingMetricEntity>,
    private readonly datasets: DatasetsService,
    @Inject(ML_SERVICE_PORT) private readonly ml: MlServicePort,
  ) {}

  /**
   * Reconciliación al arrancar: el polling vive en memoria, así que un reinicio
   * de la API dejaría jobs `queued|running` huérfanos. Los que tienen `mlJobId`
   * reanudan el polling (si el ML también se reinició, su registro en memoria
   * dará 404 y el límite de fallos los marcará failed); los que no, fallan ya.
   */
  async onModuleInit(): Promise<void> {
    try {
      const orphans = await this.jobs.find({ where: { status: In(['queued', 'running']) } });
      for (const job of orphans) {
        if (job.mlJobId) {
          this.logger.warn(`Reanudando polling del job ${job.id} (ML job ${job.mlJobId})`);
          void this.pollJob(job.id, job.mlJobId, job.modelVersionId);
        } else {
          await this.fail(job.id, job.modelVersionId, 'Job huérfano tras reinicio de la API');
        }
      }
    } catch (err) {
      this.logger.warn(`Reconciliación de jobs al arrancar falló: ${(err as Error).message}`);
    }
    // En producción el servicio ML puede arrancar con el modelo de Hugging Face
    // ya cargado. En ese caso no debe recibir una ruta local histórica de la API.
    try {
      const health = await this.ml.health();
      if (health.components?.beto?.ready || health.components?.beto?.repo) {
        this.logger.log(
          `Modelo remoto configurado${health.components.beto.repo ? `: ${health.components.beto.repo}` : ''}`,
        );
        return;
      }
      const active = await this.getActive();
      if (active?.artifactPath) {
        await this.ml.loadModel(active.artifactPath);
        this.logger.log(`Modelo activo restaurado: ${active.versionTag}`);
      }
    } catch (err) {
      this.logger.warn(`No se pudo restaurar el modelo activo: ${(err as Error).message}`);
    }
  }

  // --------------------------------------------------------------- Training
  async createJob(dto: CreateTrainingJobDto, userId: string): Promise<TrainingJobEntity> {
    const dataset = await this.datasets.findOneOrFail(dto.datasetId);
    const items = await this.datasets.getItems(dataset.id);
    if (!items.length) throw new BadRequestException('El dataset no tiene items');

    const labels = [...new Set(items.map((i) => i.labelKey))].sort();
    if (labels.length < 2) throw new BadRequestException('Se necesitan al menos 2 clases para entrenar');

    // base_model: versión padre (incremental) o BETO base.
    let baseModel = BETO;
    let parentVersionId: string | null = null;
    if (dto.parentVersionId) {
      const parent = await this.versions.findOne({ where: { id: dto.parentVersionId, isDeleted: false } });
      if (!parent?.artifactPath) throw new BadRequestException('La versión padre no tiene artefacto');
      baseModel = parent.artifactPath;
      parentVersionId = parent.id;
    }

    const versionTag = dto.versionTag ?? `v${(await this.versions.count()) + 1}`;
    const artifactPath = `storage/models/${versionTag}`;
    const hyperparams = {
      epochs: dto.hyperparams?.epochs ?? 4,
      lr: dto.hyperparams?.lr ?? 2e-5,
      batch_size: dto.hyperparams?.batch_size ?? 8,
      max_len: dto.hyperparams?.max_len ?? 192,
      seed: dto.hyperparams?.seed ?? 42,
    };

    const version = await this.versions.save(
      this.versions.create({
        versionTag,
        datasetId: dataset.id,
        projectId: dataset.projectId ?? null,
        baseModel,
        parentVersionId,
        hyperparams,
        artifactPath,
        status: 'training',
        createdUserId: userId,
        updatedUserId: userId,
      }),
    );

    const job = await this.jobs.save(
      this.jobs.create({ modelVersionId: version.id, datasetId: dataset.id, status: 'queued', progress: 0 }),
    );

    const mlItems: MlDatasetItem[] = items.map((i) => ({
      text: i.text,
      label: i.labelKey,
      split: i.split,
    }));

    try {
      const { job_id } = await this.ml.train({
        version_tag: versionTag,
        labels,
        items: mlItems,
        base_model: baseModel,
        hyperparams,
        output_dir: artifactPath,
      });
      await this.jobs.update(job.id, { mlJobId: job_id, status: 'running', startedAt: new Date() });
      void this.pollJob(job.id, job_id, version.id);
    } catch (err) {
      await this.fail(job.id, version.id, (err as Error).message);
    }

    return this.jobs.findOneByOrFail({ id: job.id });
  }

  /**
   * Registra una versión entrenada fuera del sistema (Colab/Kaggle). Los pesos
   * deben estar ya descomprimidos en el servicio ML bajo `artifactPath`; la
   * validación real del artefacto la hace `activate` vía `ml.loadModel`.
   */
  async importVersion(dto: ImportModelDto, userId: string): Promise<ModelVersionEntity> {
    const versionTag = dto.versionTag ?? `v${(await this.versions.count()) + 1}`;
    const duplicate = await this.versions.findOne({ where: { versionTag, isDeleted: false } });
    if (duplicate) throw new ConflictException(`Ya existe una versión con tag ${versionTag}`);

    let baseModel = BETO;
    let parentVersionId: string | null = null;
    if (dto.parentVersionId) {
      const parent = await this.versions.findOne({ where: { id: dto.parentVersionId, isDeleted: false } });
      if (!parent?.artifactPath) throw new BadRequestException('La versión padre no tiene artefacto');
      baseModel = parent.artifactPath;
      parentVersionId = parent.id;
    }
    if (dto.datasetId) await this.datasets.findOneOrFail(dto.datasetId);

    const version = await this.versions.save(
      this.versions.create({
        versionTag,
        datasetId: dto.datasetId ?? null,
        baseModel,
        parentVersionId,
        hyperparams: dto.hyperparams ? { ...dto.hyperparams } : null,
        artifactPath: dto.artifactPath,
        status: 'ready',
        createdUserId: userId,
        updatedUserId: userId,
      }),
    );

    if (dto.metrics) await this.saveMetrics(version.id, dto.metrics);
    this.logger.log(`Versión ${versionTag} importada (artefacto: ${dto.artifactPath})`);
    return version;
  }

  /** Espeja el estado del job del servicio ML en la tabla training_jobs (polling in-process). */
  private async pollJob(jobId: string, mlJobId: string, versionId: string): Promise<void> {
    let failures = 0;
    const tick = async () => {
      try {
        const s = await this.ml.getJob(mlJobId);
        failures = 0;
        await this.jobs.update(jobId, {
          status: s.status,
          progress: s.progress ?? 0,
          currentEpoch: s.current_epoch ?? null,
        });

        if (s.status === 'done') {
          if (s.metrics) await this.saveMetrics(versionId, s.metrics);
          await this.versions.update(versionId, {
            status: 'ready',
            artifactPath: s.artifact_path ?? undefined,
          });
          await this.jobs.update(jobId, { finishedAt: new Date(), progress: 100 });
          this.logger.log(`Entrenamiento ${versionId} OK (f1=${s.metrics?.f1_macro?.toFixed(3)})`);
          // Si es el primer modelo, actívalo automáticamente. El artifact_path del
          // status puede faltar: usa como fallback el persistido en la versión.
          const version = await this.versions.findOneBy({ id: versionId });
          await this.maybeActivateFirst(versionId, s.artifact_path ?? version?.artifactPath ?? undefined);
          return;
        }
        if (s.status === 'failed' || s.status === 'cancelled') {
          await this.fail(jobId, versionId, s.error ?? 'Job fallido en el servicio ML');
          return;
        }
      } catch (err) {
        failures += 1;
        this.logger.warn(
          `Poll de job ${mlJobId} falló (${failures}/${MAX_POLL_FAILURES}): ${(err as Error).message}`,
        );
        if (failures >= MAX_POLL_FAILURES) {
          await this.fail(jobId, versionId, `Servicio ML inalcanzable tras ${MAX_POLL_FAILURES} intentos`);
          return;
        }
      }
      setTimeout(tick, POLL_MS);
    };
    setTimeout(tick, POLL_MS);
  }

  private async fail(jobId: string, versionId: string, error: string): Promise<void> {
    await this.jobs.update(jobId, { status: 'failed', error, finishedAt: new Date() });
    await this.versions.update(versionId, { status: 'failed' });
    this.logger.error(`Entrenamiento ${versionId} falló: ${error}`);
  }

  private async saveMetrics(versionId: string, m: MlMetrics): Promise<void> {
    await this.metrics.save(
      this.metrics.create({
        modelVersionId: versionId,
        split: m.split ?? 'test',
        accuracy: m.accuracy,
        precisionMacro: m.precision_macro,
        recallMacro: m.recall_macro,
        f1Macro: m.f1_macro,
        f1Weighted: m.f1_weighted ?? null,
        f1MacroCi95: m.f1_macro_ci95 ?? null,
        resultsBySourceType: m.results_by_source_type ?? null,
        baselineName: m.baseline?.name ?? null,
        baselineF1Macro: m.baseline?.f1_macro ?? null,
        baselineDatasetSha256: m.baseline?.dataset_sha256 ?? null,
        exceedsBaseline: m.baseline ? m.f1_macro > m.baseline.f1_macro : null,
        perClassMetrics: m.per_class,
        confusionMatrix: { labels: m.labels, matrix: m.confusion_matrix },
      }),
    );
    await this.versions.update(versionId, {
      recommendationStatus: isModelRecommended(m) ? 'recommended' : 'experimental',
    });
  }

  private async maybeActivateFirst(versionId: string, artifactPath?: string): Promise<void> {
    const activeCount = await this.versions.count({ where: { isActive: true, isDeleted: false } });
    const candidate = await this.versions.findOne({ where: { id: versionId, isDeleted: false } });
    if (activeCount === 0 && artifactPath && candidate?.recommendationStatus === 'recommended') {
      try {
        await this.ml.loadModel(artifactPath);
        await this.versions.update(versionId, { isActive: true });
      } catch (err) {
        this.logger.warn(`No se pudo autoactivar ${versionId}: ${(err as Error).message}`);
      }
    }
  }

  listJobs(): Promise<TrainingJobEntity[]> {
    return this.jobs.find({ order: { createdAt: 'DESC' } });
  }

  async getJob(id: string): Promise<TrainingJobEntity> {
    const j = await this.jobs.findOne({ where: { id } });
    if (!j) throw new NotFoundException('Job no encontrado');
    return j;
  }

  // --------------------------------------------------------------- Versions
  listVersions(): Promise<ModelVersionEntity[]> {
    return this.versions.find({ where: { isDeleted: false }, order: { createdAt: 'DESC' } });
  }

  getActive(): Promise<ModelVersionEntity | null> {
    return this.versions.findOne({ where: { isActive: true, isDeleted: false } });
  }

  async activate(id: string, allowExperimental = false): Promise<ModelVersionEntity> {
    if (!allowExperimental) {
      const candidate = await this.versions.findOne({ where: { id, isDeleted: false } });
      if (candidate?.recommendationStatus !== 'recommended')
        throw new BadRequestException('Solo un administrador puede activar un modelo experimental');
    }
    const version = await this.versions.findOne({ where: { id, isDeleted: false } });
    if (!version) throw new NotFoundException('Versión no encontrada');
    if (version.status !== 'ready' || !version.artifactPath)
      throw new BadRequestException('La versión no está lista');

    // loadModel primero: valida el artefacto antes de tocar la BD. Los dos
    // UPDATE van en una transacción para no quedar nunca sin versión activa.
    // Un fallo aquí (ruta mal escrita en un import, pesos faltantes) se traduce
    // a 400 con contexto en vez del 500 opaco del wrap genérico del adaptador.
    try {
      await this.ml.loadModel(version.artifactPath);
    } catch (err) {
      throw new BadRequestException(
        `No se pudo cargar el modelo (${version.artifactPath}). ¿Están los pesos en el servicio ML? ` +
          `Detalle: ${(err as Error).message}`,
      );
    }
    await this.versions.manager.transaction(async (em) => {
      await em.update(ModelVersionEntity, { isActive: true }, { isActive: false });
      await em.update(ModelVersionEntity, { id }, { isActive: true });
    });
    return this.versions.findOneByOrFail({ id });
  }

  // --------------------------------------------------------------- Metrics
  async getMetrics(versionId: string): Promise<TrainingMetricEntity[]> {
    return this.metrics.find({ where: { modelVersionId: versionId }, order: { createdAt: 'DESC' } });
  }

  async compare(versionIds: string[]): Promise<Array<{ version: ModelVersionEntity; metrics: TrainingMetricEntity | null }>> {
    const out = [];
    for (const id of versionIds) {
      const version = await this.versions.findOne({ where: { id, isDeleted: false } });
      if (!version) continue;
      const metrics = await this.metrics.findOne({ where: { modelVersionId: id }, order: { createdAt: 'DESC' } });
      out.push({ version, metrics: metrics ?? null });
    }
    return out;
  }
}
