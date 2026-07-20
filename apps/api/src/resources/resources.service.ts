import { BadRequestException, ConflictException, ForbiddenException, Inject, Injectable, Logger, NotFoundException, OnModuleDestroy, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { InjectRepository } from '@nestjs/typeorm';
import { createHash, randomUUID } from 'node:crypto';
import { extname } from 'node:path';
import { Queue, Worker } from 'bullmq';
import { DataSource, Repository } from 'typeorm';
import { ML_SERVICE_PORT, MlServicePort, MlTranscriptUnavailable } from '../ml/ml-service.port';
import { CreateProjectDto, CreateYoutubeResourceDto, PdfMetadataDto, ReviewSegmentDto, UpdateResourceMetadataDto } from './dto/resource.dto';
import { ProjectEntity } from './entities/project.entity';
import { ResourceSegmentEntity } from './entities/resource-segment.entity';
import { ResourceEntity } from './entities/resource.entity';
import { supportedEvidence } from './evidence-support.util';
import { FileStorageService } from './storage/file-storage.service';

interface ProcessResourceJob {
  resourceId: string;
  userId: string;
  runId: string;
}

export interface HistoricalSearchFilters {
  person?: string;
  place?: string;
  yearStart?: number;
  yearEnd?: number;
  label?: string;
}

@Injectable()
export class ResourcesService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(ResourcesService.name);
  private processingQueue?: Queue<ProcessResourceJob>;
  private processingWorker?: Worker<ProcessResourceJob>;
  private databaseQueue: Promise<void> = Promise.resolve();

  constructor(
    @InjectRepository(ProjectEntity) private readonly projects: Repository<ProjectEntity>,
    @InjectRepository(ResourceEntity) private readonly resources: Repository<ResourceEntity>,
    @InjectRepository(ResourceSegmentEntity) private readonly segments: Repository<ResourceSegmentEntity>,
    @Inject(ML_SERVICE_PORT) private readonly ml: MlServicePort,
    private readonly dataSource: DataSource,
    private readonly config: ConfigService,
    private readonly storage: FileStorageService,
  ) {}

  async onModuleInit() {
    if (this.config.get<string>('PROCESSING_QUEUE_DRIVER', 'redis') === 'database') {
      try {
        await this.recoverDatabaseJobs();
      } catch (error) {
        this.logger.warn(`La recuperación esperará al bootstrap de BD: ${error instanceof Error ? error.message : error}`);
        setTimeout(() => {
          void this.recoverDatabaseJobs().catch((retryError) =>
            this.logger.error(`No se recuperó la cola: ${retryError instanceof Error ? retryError.message : retryError}`),
          );
        }, 5_000);
      }
      this.logger.log('Procesamiento persistente configurado sobre PostgreSQL');
      return;
    }
    const redisUrl = new URL(this.config.get<string>('REDIS_URL', 'redis://localhost:6379'));
    const connection = {
      host: redisUrl.hostname,
      port: Number(redisUrl.port || 6379),
      username: redisUrl.username || undefined,
      password: redisUrl.password ? decodeURIComponent(redisUrl.password) : undefined,
      db: redisUrl.pathname.length > 1 ? Number(redisUrl.pathname.slice(1)) : 0,
    };
    this.processingQueue = new Queue<ProcessResourceJob>('resource-processing', {
      connection,
      defaultJobOptions: {
        attempts: 3,
        backoff: { type: 'exponential', delay: 2000 },
        removeOnComplete: { age: 86400, count: 1000 },
        removeOnFail: { age: 604800, count: 1000 },
      },
    });
    this.processingWorker = new Worker<ProcessResourceJob>(
      'resource-processing',
      async (job) => {
        const resource = await this.findOne(job.data.resourceId);
        try {
          await this.markRunProcessing(job.data.runId);
          await this.runProcessing(resource, job.data.userId, job.data.runId);
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          const finalAttempt = job.attemptsMade + 1 >= Number(job.opts.attempts || 1);
          await this.resources.update(resource.id, {
            processingStatus: finalAttempt ? 'failed' : 'processing',
            processingError: finalAttempt ? message : `Intento ${job.attemptsMade + 1} falló: ${message}`,
            updatedUserId: job.data.userId,
          });
          await this.dataSource.query(
            `UPDATE tfm_schema.resource_processing_runs
             SET status = 'failed', error = $2, finished_at = now() WHERE id = $1`,
            [job.data.runId, message],
          );
          throw error instanceof Error ? error : new Error(message);
        }
      },
      { connection, concurrency: 1 },
    );
    this.processingWorker.on('failed', (job, error) => {
      this.logger.error(`Procesamiento ${job?.id || 'desconocido'} falló: ${error.message}`);
    });
  }

  async onModuleDestroy() {
    await this.processingWorker?.close();
    await this.processingQueue?.close();
    await this.databaseQueue.catch(() => undefined);
  }

  listProjects(user: { id: string; role: string }) {
    if (user.role === 'admin') return this.projects.find({ where: { isDeleted: false }, order: { createdAt: 'ASC' } });
    return this.dataSource.query(
      `SELECT p.id, p.name, p.description, p.period_start AS "periodStart",
              p.period_end AS "periodEnd", p.is_public AS "isPublic",
              p.created_at AS "createdAt", p.updated_at AS "updatedAt"
       FROM tfm_schema.projects p
       JOIN tfm_schema.project_memberships pm ON pm.project_id = p.id
       WHERE pm.user_id = $1 AND p.is_deleted = false ORDER BY p.created_at`,
      [user.id],
    );
  }

  async createProject(dto: CreateProjectDto, userId: string) {
    if (dto.periodStart && dto.periodEnd && dto.periodStart > dto.periodEnd) {
      throw new BadRequestException('El año inicial no puede ser mayor al final');
    }
    const project = await this.projects.save(this.projects.create({ ...dto, createdUserId: userId, updatedUserId: userId }));
    await this.dataSource.query(
      `INSERT INTO tfm_schema.project_memberships(project_id, user_id, role)
       VALUES ($1, $2, 'curator') ON CONFLICT (project_id, user_id) DO NOTHING`,
      [project.id, userId],
    );
    return project;
  }

  async dashboard(projectId: string, user: { id: string; role: string }) {
    await this.project(projectId, user);
    const rows = await this.dataSource.query(
      `SELECT
        count(DISTINCT r.id)::int AS resources,
        count(s.id)::int AS segments,
        count(s.id) FILTER (WHERE s.review_status = 'reviewed')::int AS reviewed,
        count(s.id) FILTER (WHERE s.review_status = 'pending')::int AS pending
       FROM tfm_schema.resources r
       LEFT JOIN tfm_schema.resource_segments s ON s.resource_id = r.id AND s.is_deleted = false
       WHERE r.project_id = $1 AND r.is_deleted = false`,
      [projectId],
    );
    return rows[0];
  }

  async createYoutube(projectId: string, dto: CreateYoutubeResourceDto, userId: string) {
    await this.project(projectId, { id: userId, role: 'collaborator' });
    await this.assertDemoQuota(userId);
    const existing = await this.resources.findOne({ where: { projectId, sourceUrl: dto.url, isDeleted: false } });
    if (existing) throw new ConflictException('Ese video ya existe en el proyecto');
    return this.resources.save(this.resources.create({
      projectId,
      type: 'youtube',
      title: dto.title,
      author: dto.author,
      sourceUrl: dto.url,
      rightsConfirmed: dto.rightsConfirmed,
      processingStatus: 'pending',
      createdUserId: userId,
      updatedUserId: userId,
    }));
  }

  async createPdf(projectId: string, dto: PdfMetadataDto, file: { buffer: Buffer; size: number; mimetype: string; originalname: string }, userId: string) {
    await this.project(projectId, { id: userId, role: 'collaborator' });
    await this.assertDemoQuota(userId);
    if (!file) throw new BadRequestException('Selecciona un archivo PDF');
    const maxPdfMb = this.config.get<string>('DEMO_MODE') === 'true'
      ? Number(this.config.get<string>('DEMO_MAX_PDF_MB', '10'))
      : 50;
    if (file.size > maxPdfMb * 1024 * 1024) throw new BadRequestException(`El PDF supera el límite de ${maxPdfMb} MB`);
    if (file.mimetype !== 'application/pdf' || file.buffer.subarray(0, 4).toString() !== '%PDF') {
      throw new BadRequestException('El archivo no es un PDF válido');
    }
    const checksum = createHash('sha256').update(file.buffer).digest('hex');
    const existing = await this.resources.findOne({ where: { projectId, checksum, isDeleted: false } });
    if (existing) throw new ConflictException('Ese PDF ya existe en el proyecto');
    const safeName = `${randomUUID()}${extname(file.originalname).toLowerCase() || '.pdf'}`;
    const stored = await this.storage.put(`${projectId}/${safeName}`, file.buffer, file.mimetype);
    return this.resources.save(this.resources.create({
      projectId,
      type: 'pdf',
      title: dto.title,
      author: dto.author,
      sourceUrl: dto.sourceUrl,
      license: dto.license,
      rightsConfirmed: dto.rightsConfirmed,
      storagePath: stored.legacyPath,
      storageProvider: stored.provider,
      storageKey: stored.key,
      originalFilename: file.originalname,
      mimeType: file.mimetype,
      sizeBytes: String(file.size),
      checksum,
      processingStatus: 'pending',
      createdUserId: userId,
      updatedUserId: userId,
    }));
  }

  async list(projectId: string, user: { id: string; role: string }) {
    await this.project(projectId, user);
    return this.resources.find({ where: { projectId, isDeleted: false }, order: { createdAt: 'DESC' } });
  }

  async setCorpusStatus(
    resourceId: string,
    dto: { status: 'candidate' | 'included' | 'excluded'; sourceStyle?: string; notes?: string },
    user: { id: string; role: string },
  ) {
    if (!['curador', 'admin'].includes(user.role)) throw new ForbiddenException('Solo un curador puede seleccionar el corpus');
    const resource = await this.findOne(resourceId, user);
    if (dto.status === 'included' && resource.processingStatus !== 'ready')
      throw new BadRequestException('Procesa correctamente la fuente antes de incluirla en el corpus');
    await this.resources.update(resourceId, {
      corpusStatus: dto.status,
      sourceStyle: dto.sourceStyle ?? resource.sourceStyle,
      corpusNotes: dto.notes ?? resource.corpusNotes,
      updatedUserId: user.id,
    });
    await this.audit(user.id, 'resource.corpus_status_changed', 'resource', resourceId, dto);
    return this.findOne(resourceId, user);
  }

  async findOne(id: string, user?: { id: string; role: string }) {
    const resource = await this.resources.findOne({ where: { id, isDeleted: false } });
    if (!resource) throw new NotFoundException('Fuente no encontrada');
    if (user) await this.project(resource.projectId, user);
    return resource;
  }

  async updateMetadata(
    id: string,
    dto: UpdateResourceMetadataDto,
    user: { id: string; role: string },
  ) {
    const resource = await this.findOne(id, user);
    if (!dto.title && dto.author === undefined && dto.license === undefined && dto.sourceUrl === undefined) {
      throw new BadRequestException('Indica al menos un metadato para actualizar');
    }
    await this.resources.update(id, {
      title: dto.title ?? resource.title,
      author: dto.author ?? resource.author,
      license: dto.license ?? resource.license,
      sourceUrl: dto.sourceUrl ?? resource.sourceUrl,
      updatedUserId: user.id,
    });
    await this.audit(user.id, 'resource.metadata_updated', 'resource', id, dto);
    return this.findOne(id, user);
  }

  async pdfFile(id: string, publicOnly = false, user?: { id: string; role: string }) {
    const resource = publicOnly
      ? await this.resources.findOne({ where: { id, type: 'pdf', filePublicationStatus: 'approved', isDeleted: false } })
      : await this.resources.findOne({ where: { id, type: 'pdf', isDeleted: false } });
    if (!resource || (!resource.storagePath && !resource.storageKey)) throw new NotFoundException('Documento PDF no encontrado');
    if (!publicOnly && user) await this.project(resource.projectId, user);
    try {
      const content = await this.storage.get(resource.storageProvider, resource.storageKey, resource.storagePath);
      return {
        stream: content,
        filename: (resource.originalFilename || `${resource.title}.pdf`).replace(/[\r\n"]/g, ''),
      };
    } catch (error) {
      this.logger.warn(`Documento ${id} no disponible: ${error instanceof Error ? error.message : error}`);
      throw new NotFoundException('El archivo PDF ya no está disponible');
    }
  }

  async process(id: string, userId: string) {
    const resource = await this.findOne(id);
    await this.project(resource.projectId, { id: userId, role: 'collaborator' });
    if (resource.processingStatus === 'processing') throw new ConflictException('La fuente ya se está procesando');
    await this.resources.update(id, { processingStatus: 'processing', processingError: null, updatedUserId: userId });
    try {
      const runs = await this.dataSource.query(
        `INSERT INTO tfm_schema.resource_processing_runs(resource_id, created_user_id, status)
         VALUES ($1, $2, 'queued') RETURNING id`,
        [id, userId],
      );
      const payload = { resourceId: id, userId, runId: runs[0].id };
      if (this.config.get<string>('PROCESSING_QUEUE_DRIVER', 'redis') === 'database') {
        this.enqueueDatabaseJob(payload);
        return { accepted: true, resourceId: id, jobId: runs[0].id, status: 'processing' };
      }
      const job = await this.processingQueue!.add('process-resource', payload, {
        jobId: `${id}-${Date.now()}`,
      });
      return { accepted: true, resourceId: id, jobId: job.id, status: 'processing' };
    } catch (error) {
      await this.resources.update(id, { processingStatus: 'pending', processingError: 'No se pudo encolar el trabajo' });
      throw error;
    }
  }

  private enqueueDatabaseJob(payload: ProcessResourceJob): void {
    this.databaseQueue = this.databaseQueue
      .then(() => this.executeDatabaseJob(payload))
      .catch((error) => this.logger.error(`Cola PostgreSQL: ${error instanceof Error ? error.message : error}`));
  }

  private async executeDatabaseJob(payload: ProcessResourceJob): Promise<void> {
    const resource = await this.findOne(payload.resourceId);
    try {
      await this.markRunProcessing(payload.runId);
      await this.runProcessing(resource, payload.userId, payload.runId);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      await this.resources.update(resource.id, {
        processingStatus: 'failed',
        processingError: message,
        updatedUserId: payload.userId,
      });
      await this.dataSource.query(
        `UPDATE tfm_schema.resource_processing_runs
         SET status = 'failed', error = $2, finished_at = now() WHERE id = $1`,
        [payload.runId, message],
      );
      throw error;
    }
  }

  private markRunProcessing(runId: string) {
    return this.dataSource.query(
      `UPDATE tfm_schema.resource_processing_runs
       SET status = 'processing', error = NULL, started_at = now(), finished_at = NULL
       WHERE id = $1`,
      [runId],
    );
  }

  private async recoverDatabaseJobs(): Promise<void> {
    const rows = await this.dataSource.query(
      `SELECT pr.id AS "runId", pr.resource_id AS "resourceId", pr.created_user_id AS "userId"
       FROM tfm_schema.resource_processing_runs pr
       JOIN tfm_schema.resources r ON r.id = pr.resource_id
       WHERE pr.status IN ('queued', 'processing') AND r.is_deleted = false
       ORDER BY pr.started_at`,
    );
    for (const row of rows) {
      if (!row.userId) {
        await this.dataSource.query(
          `UPDATE tfm_schema.resource_processing_runs
           SET status = 'failed', error = 'Ejecución sin usuario recuperable', finished_at = now()
           WHERE id = $1`,
          [row.runId],
        );
        continue;
      }
      this.enqueueDatabaseJob(row as ProcessResourceJob);
    }
  }

  private async runProcessing(resource: ResourceEntity, userId: string, runId: string) {
    if (resource.type === 'pdf') {
      const content = await this.storage.get(resource.storageProvider, resource.storageKey, resource.storagePath);
      const result = await this.ml.extractPdf(content, resource.originalFilename || 'documento.pdf');
      const created = result.segments.map((s) => this.segments.create({
        resourceId: resource.id,
        idx: s.idx,
        locatorType: 'page',
        pageStart: s.page_start,
        pageEnd: s.page_end,
        text: s.text,
      }));
      const saved = await this.replaceActiveSegments(resource.id, created);
      await Promise.all([this.suggestLabels(saved), this.embedSegments(saved), this.enrichEntities(saved)]);
    } else {
      let transcript;
      try {
        transcript = await this.ml.transcribeSubtitles(resource.sourceUrl!);
      } catch (err) {
        if (!(err instanceof MlTranscriptUnavailable)) throw err;
        transcript = await this.ml.transcribeAudio(resource.sourceUrl!);
      }
      const durationSec = transcript.cues.reduce(
        (maximum, cue) => Math.max(maximum, cue.start + cue.duration),
        0,
      );
      if (durationSec > 2 * 60 * 60) {
        throw new BadRequestException('El video supera el límite de dos horas');
      }
      // Ventanas sin solape para que el corpus no duplique texto entre ejemplos.
      const result = await this.ml.segment(transcript.cues, { window_sec: 75, overlap_sec: 0 });
      const created = result.segments
        .filter((s) => {
          const spokenText = s.text.replace(/\[[^\]]+\]/g, ' ').replace(/\s+/g, ' ').trim();
          return spokenText.split(' ').filter((word) => word.replace(/[^\p{L}\p{N}]/gu, '').length > 1).length >= 8;
        })
        .map((s) => this.segments.create({
        resourceId: resource.id,
        idx: s.idx,
        locatorType: 'timestamp',
        startSec: s.start_sec,
        endSec: s.end_sec,
        text: s.text,
      }));
      const saved = await this.replaceActiveSegments(resource.id, created);
      await this.resources.update(resource.id, { language: transcript.language });
      await Promise.all([this.suggestLabels(saved), this.embedSegments(saved), this.enrichEntities(saved)]);
    }
    await this.resources.update(resource.id, { processingStatus: 'ready', processingError: null, updatedUserId: userId });
    const segmentCount = await this.segments.count({ where: { resourceId: resource.id, isDeleted: false } });
    await this.dataSource.query(
      `UPDATE tfm_schema.resource_processing_runs
       SET status = 'ready', segment_count = $2, finished_at = now() WHERE id = $1`,
      [runId, segmentCount],
    );
  }

  private replaceActiveSegments(resourceId: string, created: ResourceSegmentEntity[]) {
    return this.dataSource.transaction(async (manager) => {
      await manager.update(ResourceSegmentEntity, { resourceId, isDeleted: false }, { isDeleted: true });
      return manager.getRepository(ResourceSegmentEntity).save(created);
    });
  }

  private async suggestLabels(segments: ResourceSegmentEntity[]) {
    if (!segments.length) return;
    try {
      const predictions = await this.ml.infer(segments.map((s) => s.text));
      await Promise.all(segments.map((segment, i) => this.segments.update(segment.id, {
        suggestedLabelKey: predictions[i]?.label,
        suggestedConfidence: predictions[i]?.confidence,
      })));
    } catch {
      // La fuente sigue siendo útil aunque aún no exista un modelo BETO activo.
    }
  }

  /**
   * Vuelve a ejecutar BETO sobre los fragmentos vigentes sin retranscribir ni
   * reemplazar el contenido. Conserva todas las revisiones humanas existentes.
   */
  async classifySegments(resourceId: string, user: { id: string; role: string }) {
    const resource = await this.findOne(resourceId, user);
    if (resource.processingStatus !== 'ready') {
      throw new BadRequestException('La fuente debe terminar de procesarse antes de analizar sus subtemas');
    }
    const segments = await this.segments.find({
      where: { resourceId, isDeleted: false },
      order: { idx: 'ASC' },
    });
    if (!segments.length) throw new BadRequestException('La fuente no tiene fragmentos para clasificar');

    let predictions;
    try {
      predictions = await this.ml.infer(segments.map((segment) => segment.text));
    } catch (error) {
      throw new BadRequestException(
        `No se pudieron analizar los subtemas. Comprueba que exista un modelo activo. Detalle: ${
          error instanceof Error ? error.message : error
        }`,
      );
    }
    await this.dataSource.transaction(async (manager) => {
      for (let index = 0; index < segments.length; index += 1) {
        const prediction = predictions[index];
        if (!prediction) continue;
        await manager.update(ResourceSegmentEntity, segments[index].id, {
          suggestedLabelKey: prediction.label,
          suggestedConfidence: prediction.confidence,
        });
      }
    });
    await this.audit(user.id, 'resource.segments_classified', 'resource', resourceId, {
      segmentCount: segments.length,
    });
    return { resourceId, classified: predictions.length };
  }

  private async embedSegments(segments: ResourceSegmentEntity[]) {
    try {
      for (let offset = 0; offset < segments.length; offset += 64) {
        const batch = segments.slice(offset, offset + 64);
        const result = await this.ml.embed(batch.map((segment) => segment.text));
        await Promise.all(batch.map((segment, index) => this.dataSource.query(
          `UPDATE tfm_schema.resource_segments
           SET embedding = $2::vector, embedding_model = $3, embedded_at = now()
           WHERE id = $1`,
          [segment.id, JSON.stringify(result.embeddings[index]), result.model],
        )));
      }
    } catch (error) {
      this.logger.warn(`La fuente quedó sin embeddings: ${error instanceof Error ? error.message : error}`);
    }
  }

  private async enrichEntities(segments: ResourceSegmentEntity[]) {
    try {
      for (let offset = 0; offset < segments.length; offset += 32) {
        const batch = segments.slice(offset, offset + 32);
        const result = await this.ml.extractEntities(batch.map((segment) => segment.text));
        const inserts = batch.flatMap((segment, index) =>
          (result.results[index] || []).map((mention) => this.dataSource.query(
            `INSERT INTO tfm_schema.entity_mentions(
               resource_segment_id, entity_type, mention_text, normalized_value,
               char_start, char_end, confidence, year_start, year_end, extraction_method
               , is_out_of_scope
             ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`,
            [
              segment.id,
              mention.type,
              mention.text.slice(0, 300),
              mention.normalized_value.slice(0, 300),
              mention.start,
              mention.end,
              mention.confidence,
              mention.year_start ?? null,
              mention.year_end ?? null,
              mention.method,
              mention.out_of_scope ?? false,
            ],
          )),
        );
        await Promise.all(inserts);
        if (!result.model_available && result.error) {
          this.logger.warn(`BETO-NER no disponible; se conservaron las fechas por reglas: ${result.error}`);
        }
      }
    } catch (error) {
      this.logger.warn(`La fuente quedó sin enriquecimiento de entidades: ${error instanceof Error ? error.message : error}`);
    }
  }

  async listSegments(resourceId: string, user?: { id: string; role: string }) {
    const resource = await this.findOne(resourceId, user);
    return this.segments.find({ where: { resourceId: resource.id, isDeleted: false }, order: { idx: 'ASC' } });
  }

  async listSegmentsPage(
    projectId: string,
    resourceId: string,
    query: { page?: number; limit?: number; status?: string; label?: string; sort?: string; campaignId?: string },
    user: { id: string; role: string },
  ) {
    await this.project(projectId, user);
    const resource = await this.resources.findOne({ where: { id: resourceId, projectId, isDeleted: false } });
    if (!resource) throw new NotFoundException('Fuente no encontrada en este proyecto');
    const page = Math.max(1, query.page || 1);
    const limit = Math.min(100, Math.max(1, query.limit || 30));
    const offset = (page - 1) * limit;
    const order = query.sort === 'low_confidence'
      ? 'COALESCE(s.suggested_confidence, 0) ASC, s.idx ASC'
      : 's.idx ASC';
    const params = [resourceId, query.status || null, query.label || null, query.campaignId || null, limit, offset];
    const [items, countRows] = await Promise.all([
      this.dataSource.query(
        `SELECT s.id, s.resource_id AS "resourceId", s.idx,
                s.locator_type AS "locatorType", s.start_sec AS "startSec",
                s.end_sec AS "endSec", s.page_start AS "pageStart",
                s.page_end AS "pageEnd", s.text,
                s.suggested_label_key AS "suggestedLabelKey",
                s.suggested_confidence AS "suggestedConfidence",
                s.review_status AS "reviewStatus",
                s.reviewed_label_key AS "reviewedLabelKey",
                s.reviewed_user_id AS "reviewedUserId",
                s.reviewed_at AS "reviewedAt",
                COALESCE((SELECT jsonb_agg(jsonb_build_object(
                  'type', em.entity_type, 'text', em.mention_text,
                  'normalizedValue', em.normalized_value, 'yearStart', em.year_start,
                  'yearEnd', em.year_end, 'confidence', em.confidence,
                  'outOfScope', em.is_out_of_scope
                ) ORDER BY em.char_start)
                FROM tfm_schema.entity_mentions em
                WHERE em.resource_segment_id = s.id AND em.is_deleted = false), '[]'::jsonb) AS entities
         FROM tfm_schema.resource_segments s
         WHERE s.resource_id = $1 AND s.is_deleted = false
           AND ($2::text IS NULL OR s.review_status = $2)
           AND ($3::text IS NULL OR COALESCE(s.reviewed_label_key, s.suggested_label_key) = $3)
           AND ($4::uuid IS NULL OR EXISTS (
             SELECT 1 FROM tfm_schema.primary_annotation_samples pas
             WHERE pas.campaign_id = $4 AND pas.resource_segment_id = s.id
           ))
         ORDER BY ${order} LIMIT $5 OFFSET $6`,
        params,
      ),
      this.dataSource.query(
        `SELECT count(*)::int AS total FROM tfm_schema.resource_segments s
         WHERE s.resource_id = $1 AND s.is_deleted = false
           AND ($2::text IS NULL OR s.review_status = $2)
           AND ($3::text IS NULL OR COALESCE(s.reviewed_label_key, s.suggested_label_key) = $3)
           AND ($4::uuid IS NULL OR EXISTS (
             SELECT 1 FROM tfm_schema.primary_annotation_samples pas
             WHERE pas.campaign_id = $4 AND pas.resource_segment_id = s.id
           ))`,
        params.slice(0, 4),
      ),
    ]);
    const total = countRows[0]?.total || 0;
    return { items, page, limit, total, totalPages: Math.max(1, Math.ceil(total / limit)) };
  }

  async review(segmentId: string, dto: ReviewSegmentDto, userId: string) {
    const segment = await this.segments.findOne({ where: { id: segmentId, isDeleted: false } });
    if (!segment) throw new NotFoundException('Fragmento no encontrado');
    await this.assertSegmentAccess(segmentId, userId);
    if (dto.status === 'reviewed' && !dto.labelKey) throw new BadRequestException('Elige un subtema para confirmar');
    await this.segments.update(segmentId, {
      reviewStatus: dto.status,
      reviewedLabelKey: dto.status === 'reviewed' ? dto.labelKey : null,
      reviewedUserId: userId,
      reviewedAt: new Date(),
    });
    return this.segments.findOneByOrFail({ id: segmentId });
  }

  async bulkReview(segmentIds: string[], dto: ReviewSegmentDto, userId: string) {
    if (dto.status === 'reviewed' && !dto.labelKey) throw new BadRequestException('Elige un subtema para confirmar');
    for (const segmentId of segmentIds) await this.assertSegmentAccess(segmentId, userId);
    const result = await this.dataSource.query(
      `UPDATE tfm_schema.resource_segments
       SET review_status = $2::varchar,
           reviewed_label_key = CASE WHEN $2::varchar = 'reviewed' THEN $3::varchar ELSE NULL END,
           reviewed_user_id = $4, reviewed_at = now(), updated_at = now()
       WHERE id = ANY($1::uuid[]) AND is_deleted = false RETURNING id`,
      [segmentIds, dto.status, dto.labelKey || null, userId],
    );
    const updated = Array.isArray(result[0]) ? result[0].length : result.length;
    await this.audit(userId, 'segment.bulk_reviewed', 'resource_segment', undefined, {
      requested: segmentIds.length, updated, status: dto.status, labelKey: dto.labelKey,
    });
    return { updated };
  }

  async saveEvidenceFeedback(
    segmentId: string,
    value: 'useful' | 'irrelevant' | 'incorrect',
    note: string | undefined,
    userId: string,
  ) {
    const segment = await this.segments.findOne({ where: { id: segmentId, isDeleted: false } });
    if (!segment) throw new NotFoundException('Fragmento no encontrado');
    await this.assertSegmentAccess(segmentId, userId);
    const rows = await this.dataSource.query(
      `INSERT INTO tfm_schema.evidence_feedback(resource_segment_id, user_id, value, note)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (resource_segment_id, user_id)
       DO UPDATE SET value = EXCLUDED.value, note = EXCLUDED.note, updated_at = now()
       RETURNING id, value, note, updated_at AS "updatedAt"`,
      [segmentId, userId, value, note || null],
    );
    await this.audit(userId, 'evidence.feedback_saved', 'resource_segment', segmentId, { value });
    return rows[0];
  }

  async listSegmentEntities(segmentId: string, userId?: string) {
    const segment = await this.segments.findOne({ where: { id: segmentId, isDeleted: false } });
    if (userId) await this.assertSegmentAccess(segmentId, userId);
    if (!segment) throw new NotFoundException('Fragmento no encontrado');
    return this.dataSource.query(
      `SELECT id, entity_type AS type, mention_text AS text,
              normalized_value AS "normalizedValue", confidence,
              year_start AS "yearStart", year_end AS "yearEnd",
              extraction_method AS method, is_human AS "isHuman",
              is_out_of_scope AS "outOfScope"
       FROM tfm_schema.entity_mentions
       WHERE resource_segment_id = $1 AND is_deleted = false
       ORDER BY char_start NULLS LAST, created_at`,
      [segmentId],
    );
  }

  async replaceSegmentEntities(
    segmentId: string,
    entities: Array<{ type: string; text: string; yearStart?: number; yearEnd?: number }>,
    userId: string,
  ) {
    await this.assertSegmentAccess(segmentId, userId);
    const segment = await this.segments.findOne({ where: { id: segmentId, isDeleted: false } });
    if (!segment) throw new NotFoundException('Fragmento no encontrado');
    for (const entity of entities) {
      if (['date', 'period'].includes(entity.type) && !entity.yearStart) {
        throw new BadRequestException(`Indica el año de ${entity.text}`);
      }
      if (entity.yearStart && entity.yearEnd && entity.yearStart > entity.yearEnd) {
        throw new BadRequestException(`El periodo de ${entity.text} no es válido`);
      }
    }
    await this.dataSource.transaction(async (manager) => {
      const previous = await manager.query(
        `SELECT id FROM tfm_schema.entity_mentions
         WHERE resource_segment_id = $1 AND is_deleted = false`,
        [segmentId],
      );
      await manager.query(
        `UPDATE tfm_schema.entity_mentions SET is_deleted = true, updated_at = now()
         WHERE resource_segment_id = $1 AND is_deleted = false`,
        [segmentId],
      );
      for (const entity of entities) {
        const normalized = entity.text.normalize('NFKC').toLocaleLowerCase('es-PE').trim().replace(/\s+/g, ' ');
        await manager.query(
          `INSERT INTO tfm_schema.entity_mentions(
             resource_segment_id, entity_type, mention_text, normalized_value,
             confidence, year_start, year_end, extraction_method, is_human, created_user_id
           ) VALUES ($1, $2, $3, $4, 1, $5, $6, 'human', true, $7)`,
          [
            segmentId,
            entity.type,
            entity.text,
            normalized,
            entity.yearStart ?? null,
            entity.yearEnd ?? entity.yearStart ?? null,
            userId,
          ],
        );
      }
      await manager.query(
        `UPDATE tfm_schema.resource_segments
         SET entities_reviewed_at = now(), entities_reviewed_user_id = $2
         WHERE id = $1`,
        [segmentId, userId],
      );
      await manager.query(
        `INSERT INTO tfm_schema.audit_events(actor_user_id, action, entity_type, entity_id, metadata)
         VALUES ($1, 'segment.entities_reviewed', 'resource_segment', $2, $3::jsonb)`,
        [userId, segmentId, JSON.stringify({ previousCount: previous.length, newCount: entities.length })],
      );
    });
    return this.listSegmentEntities(segmentId);
  }

  async search(projectId: string, query: string, filters: HistoricalSearchFilters = {}, user?: { id: string; role: string }) {
    await this.project(projectId, user);
    if (query.trim().length < 3) throw new BadRequestException('Escribe al menos tres caracteres');
    const rows = await this.retrieveEvidence(projectId, query.trim(), false, filters);
    return {
      query,
      answer: rows.length
        ? `Encontré ${rows.length} fragmentos con evidencia relacionada. Revisa las citas antes de utilizarlas.`
        : 'No encuentro respaldo suficiente en las fuentes disponibles.',
      evidence: rows,
    };
  }

  async assistant(projectId: string, query: string, filters: HistoricalSearchFilters = {}, user?: { id: string; role: string }) {
    const result = await this.search(projectId, query, filters, user);
    const supported = supportedEvidence(query, result.evidence).slice(0, 5);
    if (!supported.length) return {
      ...result,
      answer: 'No encuentro respaldo suficiente en las fuentes disponibles.',
      evidence: [], citations: [], mode: 'abstained',
    };
    result.evidence = supported;
    const citations = result.evidence.map((item: { id: string; title: string; locatorType: string; startSec?: number; pageStart?: number }, index: number) => ({
      id: index + 1,
      segmentId: item.id,
      title: item.title,
      locator: item.locatorType === 'timestamp' ? { type: 'timestamp', startSec: item.startSec } : { type: 'page', page: item.pageStart },
    }));
    const extractive = result.evidence.slice(0, 3).map((item: { text: string }, index: number) => {
      const excerpt = item.text.length > 280 ? `${item.text.slice(0, 277)}…` : item.text;
      return `[${index + 1}] ${excerpt}`;
    }).join('\n\n');
    const providerUrl = this.config.get<string>('RAG_PROVIDER_URL');
    if (!providerUrl) return { ...result, answer: extractive, citations, mode: 'extractive' };
    try {
      const response = await fetch(providerUrl, {
        method: 'POST',
        headers: { 'content-type': 'application/json', authorization: `Bearer ${this.config.get<string>('RAG_PROVIDER_KEY', '')}` },
        body: JSON.stringify({ query, evidence: result.evidence.map((item: { text: string }, index: number) => ({ id: index + 1, text: item.text })) }),
      });
      const payload = await response.json() as { answer?: string };
      const answer = payload.answer || '';
      const used = [...answer.matchAll(/\[(\d+)\]/g)].map((match) => Number(match[1]));
      if (!used.length || used.some((id) => id < 1 || id > citations.length)) throw new Error('Respuesta sin citas válidas');
      return { ...result, answer, citations, mode: 'generated' };
    } catch {
      return { ...result, answer: extractive, citations, mode: 'extractive' };
    }
  }

  async listCollections(projectId: string, user: { id: string; role: string }) {
    await this.project(projectId, user);
    return this.dataSource.query(
      `SELECT c.id, c.name, c.description, c.is_public AS "isPublic", c.created_at AS "createdAt",
              count(i.id)::int AS "itemCount"
       FROM tfm_schema.collections c
       LEFT JOIN tfm_schema.collection_items i ON i.collection_id = c.id
       WHERE c.project_id = $1 AND c.is_deleted = false
       GROUP BY c.id ORDER BY c.created_at DESC`,
      [projectId],
    );
  }

  async createCollection(projectId: string, name: string, description: string | undefined, userId: string) {
    await this.project(projectId, { id: userId, role: 'collaborator' });
    const rows = await this.dataSource.query(
      `INSERT INTO tfm_schema.collections(project_id, name, description, created_user_id, updated_user_id)
       VALUES ($1, $2, $3, $4, $4) RETURNING id, name, description, is_public AS "isPublic", created_at AS "createdAt"`,
      [projectId, name, description || null, userId],
    );
    await this.audit(userId, 'collection.created', 'collection', rows[0].id);
    return rows[0];
  }

  async collection(id: string, user?: { id: string; role: string }) {
    const collections = await this.dataSource.query(
      `SELECT id, project_id AS "projectId", name, description, is_public AS "isPublic"
       FROM tfm_schema.collections WHERE id = $1 AND is_deleted = false`,
      [id],
    );
    if (!collections.length) throw new NotFoundException('Colección no encontrada');
    if (user) await this.project(collections[0].projectId, user);
    const items = await this.dataSource.query(
      `SELECT i.id, i.note, i.sort_order AS "sortOrder", s.id AS "segmentId", s.text,
              s.locator_type AS "locatorType", s.start_sec AS "startSec", s.end_sec AS "endSec",
              s.page_start AS "pageStart", s.page_end AS "pageEnd", r.title, r.type,
              r.source_url AS "sourceUrl"
       FROM tfm_schema.collection_items i
       JOIN tfm_schema.resource_segments s ON s.id = i.resource_segment_id
       JOIN tfm_schema.resources r ON r.id = s.resource_id
       WHERE i.collection_id = $1 ORDER BY i.sort_order, i.created_at`,
      [id],
    );
    return { ...collections[0], items };
  }

  async addCollectionItem(collectionId: string, segmentId: string, note: string | undefined, userId: string) {
    const target = await this.collection(collectionId);
    await this.project(target.projectId, { id: userId, role: 'collaborator' });
    await this.assertSegmentAccess(segmentId, userId);
    const rows = await this.dataSource.query(
      `INSERT INTO tfm_schema.collection_items(collection_id, resource_segment_id, note, created_user_id)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (collection_id, resource_segment_id) DO UPDATE SET note = EXCLUDED.note
       RETURNING id`,
      [collectionId, segmentId, note || null, userId],
    );
    await this.audit(userId, 'collection.item_saved', 'collection', collectionId, { segmentId });
    return { saved: true, id: rows[0].id };
  }

  async requestPublication(resourceId: string, userId: string) {
    const resource = await this.findOne(resourceId);
    await this.project(resource.projectId, { id: userId, role: 'collaborator' });
    if (!resource.rightsConfirmed) throw new BadRequestException('Confirma los derechos de uso antes de solicitar publicación');
    if (resource.processingStatus !== 'ready') throw new BadRequestException('La fuente debe estar procesada antes de publicarse');
    await this.resources.update(resourceId, { publicationStatus: 'proposed', filePublicationStatus: 'proposed', updatedUserId: userId });
    const rows = await this.dataSource.query(
      `INSERT INTO tfm_schema.publication_reviews(resource_id, requested_user_id)
       VALUES ($1, $2) RETURNING id, status, requested_at AS "requestedAt"`,
      [resourceId, userId],
    );
    await this.audit(userId, 'publication.requested', 'resource', resourceId);
    return rows[0];
  }

  async unpublish(resourceId: string, user: { id: string; role: string }) {
    if (!['curador', 'admin'].includes(user.role)) throw new ForbiddenException('Solo un curador puede retirar fuentes');
    const resource = await this.findOne(resourceId);
    await this.project(resource.projectId, user);
    await this.resources.update(resourceId, { publicationStatus: 'private', filePublicationStatus: 'private', updatedUserId: user.id });
    const approved = await this.resources.count({ where: { projectId: resource.projectId, publicationStatus: 'approved', isDeleted: false } });
    if (approved === 0) await this.projects.update(resource.projectId, { isPublic: false });
    await this.audit(user.id, 'publication.unpublished', 'resource', resourceId);
    return { status: 'private', resourceId };
  }

  listPublicationReviews(user: { id: string; role: string }) {
    if (!['curador', 'admin'].includes(user.role)) throw new ForbiddenException('Solo un curador puede ver solicitudes');
    return this.dataSource.query(
      `SELECT pr.id, pr.status, pr.requested_at AS "requestedAt", pr.note,
              r.id AS "resourceId", r.title, r.type, r.license, r.rights_confirmed AS "rightsConfirmed"
       FROM tfm_schema.publication_reviews pr
       JOIN tfm_schema.resources r ON r.id = pr.resource_id
       LEFT JOIN tfm_schema.project_memberships pm ON pm.project_id = r.project_id AND pm.user_id = $1
       WHERE pr.status = 'proposed' AND ($2 = 'admin' OR pm.user_id IS NOT NULL)
       ORDER BY pr.requested_at`,
      [user.id, user.role],
    );
  }

  async decidePublication(reviewId: string, status: 'approved' | 'rejected', note: string | undefined, user: { id: string; role: string }) {
    if (!['curador', 'admin'].includes(user.role)) throw new ForbiddenException('Solo un curador puede aprobar publicaciones');
    const pending = await this.dataSource.query(
      `SELECT pr.requested_user_id AS "requestedUserId", r.project_id AS "projectId"
       FROM tfm_schema.publication_reviews pr JOIN tfm_schema.resources r ON r.id = pr.resource_id
       WHERE pr.id = $1 AND pr.status = 'proposed'`,
      [reviewId],
    );
    if (!pending.length) throw new NotFoundException('Solicitud no encontrada');
    await this.project(pending[0].projectId, user);
    if (pending[0].requestedUserId === user.id && user.role !== 'admin')
      throw new ForbiddenException('El aportante no puede aprobar su propia publicacion');
    const rows = await this.dataSource.query(
      `UPDATE tfm_schema.publication_reviews SET status = $2, note = $3, reviewed_user_id = $4, reviewed_at = now()
       WHERE id = $1 AND status = 'proposed' RETURNING resource_id AS "resourceId"`,
      [reviewId, status, note || null, user.id],
    );
    if (!rows.length) throw new NotFoundException('Solicitud de publicación no encontrada');
    await this.resources.update(rows[0].resourceId, { publicationStatus: status, filePublicationStatus: status });
    if (status === 'approved') {
      const resource = await this.findOne(rows[0].resourceId);
      await this.projects.update(resource.projectId, { isPublic: true });
    }
    await this.audit(user.id, `publication.${status}`, 'resource', rows[0].resourceId, { note });
    return { status, resourceId: rows[0].resourceId };
  }

  publicProjects() {
    return this.projects.find({ where: { isPublic: true, isDeleted: false }, order: { createdAt: 'ASC' } });
  }

  publicResources(projectId: string) {
    return this.resources.find({
      where: { projectId, publicationStatus: 'approved', isDeleted: false },
      order: { createdAt: 'DESC' },
    });
  }

  async searchFacets(projectId: string, user: { id: string; role: string }) {
    await this.project(projectId, user);
    const base = `
      FROM tfm_schema.entity_mentions em
      JOIN tfm_schema.resource_segments s ON s.id = em.resource_segment_id
      JOIN tfm_schema.resources r ON r.id = s.resource_id
      WHERE r.project_id = $1 AND r.is_deleted = false AND s.is_deleted = false
        AND em.is_deleted = false`;
    const [persons, places, years, labels] = await Promise.all([
      this.dataSource.query(
        `SELECT min(em.mention_text) AS label, em.normalized_value AS value, count(*)::int AS count
         ${base} AND em.entity_type = 'person'
         GROUP BY em.normalized_value ORDER BY count DESC, label LIMIT 30`,
        [projectId],
      ),
      this.dataSource.query(
        `SELECT min(em.mention_text) AS label, em.normalized_value AS value, count(*)::int AS count
         ${base} AND em.entity_type = 'place'
         GROUP BY em.normalized_value ORDER BY count DESC, label LIMIT 30`,
        [projectId],
      ),
      this.dataSource.query(
        `SELECT em.year_start AS value, count(*)::int AS count
         ${base} AND em.entity_type IN ('date', 'period') AND em.year_start IS NOT NULL
           AND em.is_out_of_scope = false
         GROUP BY em.year_start ORDER BY em.year_start`,
        [projectId],
      ),
      this.dataSource.query(
        `SELECT lt.key AS value, lt.name AS label, count(s.id)::int AS count
         FROM tfm_schema.resource_segments s
         JOIN tfm_schema.resources r ON r.id = s.resource_id
         JOIN tfm_schema.labels_taxonomy lt
           ON lt.key = COALESCE(s.reviewed_label_key, s.suggested_label_key)
         WHERE r.project_id = $1 AND r.is_deleted = false AND s.is_deleted = false
         GROUP BY lt.key, lt.name ORDER BY lt.sort_order`,
        [projectId],
      ),
    ]);
    return { persons, places, years, labels };
  }

  async publicSearch(projectId: string, query: string, filters: HistoricalSearchFilters = {}) {
    const project = await this.projects.findOne({ where: { id: projectId, isPublic: true, isDeleted: false } });
    if (!project) throw new NotFoundException('Proyecto público no encontrado');
    if (query.trim().length < 3) throw new BadRequestException('Escribe al menos tres caracteres');
    const rows = supportedEvidence(
      query,
      await this.retrieveEvidence(projectId, query.trim(), true, filters),
    ).slice(0, 5);
    return {
      query,
      answer: rows.length
        ? `Encontré ${rows.length} evidencias verificables en el repositorio público.`
        : 'No encuentro respaldo suficiente en las fuentes disponibles.',
      evidence: rows,
    };
  }

  private async retrieveEvidence(projectId: string, query: string, publicOnly: boolean, filters: HistoricalSearchFilters) {
    const publicationFilter = publicOnly ? `AND r.publication_status = 'approved' AND s.review_status = 'reviewed'` : '';
    const person = filters.person ? `%${filters.person.trim()}%` : null;
    const place = filters.place ? `%${filters.place.trim()}%` : null;
    const yearStart = filters.yearStart ?? null;
    const yearEnd = filters.yearEnd ?? null;
    const label = filters.label || null;
    const entityProjection = `
      COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'type', em.entity_type, 'text', em.mention_text,
          'normalizedValue', em.normalized_value,
          'yearStart', em.year_start, 'yearEnd', em.year_end,
          'confidence', em.confidence
        ) ORDER BY em.char_start)
        FROM tfm_schema.entity_mentions em
        WHERE em.resource_segment_id = s.id AND em.is_deleted = false
      ), '[]'::jsonb) AS entities`;
    try {
      const semantic = await this.ml.embed([query]);
      return await this.dataSource.query(
        `SELECT s.id, s.text, s.locator_type AS "locatorType", s.start_sec AS "startSec",
                s.end_sec AS "endSec", s.page_start AS "pageStart", s.page_end AS "pageEnd",
                r.id AS "resourceId", r.title, r.type, r.source_url AS "sourceUrl",
                (0.55 * COALESCE(GREATEST(0, 1 - (s.embedding <=> $3::vector)), 0)
                 + 0.30 * ts_rank(to_tsvector('spanish', s.text), websearch_to_tsquery('spanish', $2))
                 + 0.15 * similarity(s.text, $2)) AS score,
                (1 - (s.embedding <=> $3::vector)) AS "semanticScore",
                ${entityProjection}
         FROM tfm_schema.resource_segments s
         JOIN tfm_schema.resources r ON r.id = s.resource_id
         WHERE r.project_id = $1 ${publicationFilter}
           AND r.is_deleted = false AND s.is_deleted = false
           AND ($4::text IS NULL OR EXISTS (
             SELECT 1 FROM tfm_schema.entity_mentions ep
             WHERE ep.resource_segment_id = s.id AND ep.entity_type = 'person' AND ep.is_deleted = false
               AND ep.normalized_value ILIKE $4
           ))
           AND ($5::text IS NULL OR EXISTS (
             SELECT 1 FROM tfm_schema.entity_mentions el
             WHERE el.resource_segment_id = s.id AND el.entity_type = 'place' AND el.is_deleted = false
               AND el.normalized_value ILIKE $5
           ))
           AND (($6::int IS NULL AND $7::int IS NULL) OR EXISTS (
             SELECT 1 FROM tfm_schema.entity_mentions et
             WHERE et.resource_segment_id = s.id AND et.entity_type IN ('date', 'period') AND et.is_deleted = false
               AND et.year_start <= COALESCE($7::int, et.year_start)
               AND et.year_end >= COALESCE($6::int, et.year_end)
           ))
           AND ($8::text IS NULL OR COALESCE(s.reviewed_label_key, s.suggested_label_key) = $8)
           AND (s.embedding IS NOT NULL
                OR to_tsvector('spanish', s.text) @@ websearch_to_tsquery('spanish', $2)
                OR similarity(s.text, $2) > 0.08)
         ORDER BY score DESC NULLS LAST LIMIT 8`,
        [projectId, query, JSON.stringify(semantic.embeddings[0]), person, place, yearStart, yearEnd, label],
      );
    } catch (error) {
      this.logger.warn(`Búsqueda semántica no disponible; se usará búsqueda textual: ${error instanceof Error ? error.message : error}`);
      try {
        return await this.dataSource.query(
        `SELECT s.id, s.text, s.locator_type AS "locatorType", s.start_sec AS "startSec",
                s.end_sec AS "endSec", s.page_start AS "pageStart", s.page_end AS "pageEnd",
                r.id AS "resourceId", r.title, r.type, r.source_url AS "sourceUrl",
                (ts_rank(to_tsvector('spanish', s.text), websearch_to_tsquery('spanish', $2))
                 + similarity(s.text, $2)) AS score,
                ${entityProjection}
         FROM tfm_schema.resource_segments s
         JOIN tfm_schema.resources r ON r.id = s.resource_id
         WHERE r.project_id = $1 ${publicationFilter}
           AND r.is_deleted = false AND s.is_deleted = false
           AND ($3::text IS NULL OR EXISTS (
             SELECT 1 FROM tfm_schema.entity_mentions ep
             WHERE ep.resource_segment_id = s.id AND ep.entity_type = 'person' AND ep.is_deleted = false
               AND ep.normalized_value ILIKE $3
           ))
           AND ($4::text IS NULL OR EXISTS (
             SELECT 1 FROM tfm_schema.entity_mentions el
             WHERE el.resource_segment_id = s.id AND el.entity_type = 'place' AND el.is_deleted = false
               AND el.normalized_value ILIKE $4
           ))
           AND (($5::int IS NULL AND $6::int IS NULL) OR EXISTS (
             SELECT 1 FROM tfm_schema.entity_mentions et
             WHERE et.resource_segment_id = s.id AND et.entity_type IN ('date', 'period') AND et.is_deleted = false
               AND et.year_start <= COALESCE($6::int, et.year_start)
               AND et.year_end >= COALESCE($5::int, et.year_end)
           ))
           AND ($7::text IS NULL OR COALESCE(s.reviewed_label_key, s.suggested_label_key) = $7)
           AND (to_tsvector('spanish', s.text) @@ websearch_to_tsquery('spanish', $2)
                OR similarity(s.text, $2) > 0.08)
         ORDER BY score DESC LIMIT 8`,
          [projectId, query, person, place, yearStart, yearEnd, label],
        );
      } catch (textError) {
        this.logger.warn(
          `Búsqueda textual con pg_trgm no disponible; se usará texto completo nativo: ${textError instanceof Error ? textError.message : textError}`,
        );
        try {
          return await this.dataSource.query(
            `SELECT s.id, s.text, s.locator_type AS "locatorType", s.start_sec AS "startSec",
                    s.end_sec AS "endSec", s.page_start AS "pageStart", s.page_end AS "pageEnd",
                    r.id AS "resourceId", r.title, r.type, r.source_url AS "sourceUrl",
                    ts_rank(to_tsvector('spanish', s.text), websearch_to_tsquery('spanish', $2)) AS score,
                    ${entityProjection}
             FROM tfm_schema.resource_segments s
             JOIN tfm_schema.resources r ON r.id = s.resource_id
             WHERE r.project_id = $1 ${publicationFilter}
               AND r.is_deleted = false AND s.is_deleted = false
               AND ($3::text IS NULL OR EXISTS (
                 SELECT 1 FROM tfm_schema.entity_mentions ep
                 WHERE ep.resource_segment_id = s.id AND ep.entity_type = 'person' AND ep.is_deleted = false
                   AND ep.normalized_value ILIKE $3
               ))
               AND ($4::text IS NULL OR EXISTS (
                 SELECT 1 FROM tfm_schema.entity_mentions el
                 WHERE el.resource_segment_id = s.id AND el.entity_type = 'place' AND el.is_deleted = false
                   AND el.normalized_value ILIKE $4
               ))
               AND (($5::int IS NULL AND $6::int IS NULL) OR EXISTS (
                 SELECT 1 FROM tfm_schema.entity_mentions et
                 WHERE et.resource_segment_id = s.id AND et.entity_type IN ('date', 'period') AND et.is_deleted = false
                   AND et.year_start <= COALESCE($6::int, et.year_start)
                   AND et.year_end >= COALESCE($5::int, et.year_end)
               ))
               AND ($7::text IS NULL OR COALESCE(s.reviewed_label_key, s.suggested_label_key) = $7)
               AND to_tsvector('spanish', s.text) @@ websearch_to_tsquery('spanish', $2)
             ORDER BY score DESC LIMIT 8`,
            [projectId, query, person, place, yearStart, yearEnd, label],
          );
        } catch (nativeTextError) {
          this.logger.error(
            `No se pudo recuperar evidencia; el asistente se abstendrá: ${nativeTextError instanceof Error ? nativeTextError.message : nativeTextError}`,
          );
          return [];
        }
      }
    }
  }

  private audit(actor: string, action: string, entityType: string, entityId?: string, metadata?: unknown) {
    return this.dataSource.query(
      `INSERT INTO tfm_schema.audit_events(actor_user_id, action, entity_type, entity_id, metadata)
       VALUES ($1, $2, $3, $4, $5)`,
      [actor, action, entityType, entityId || null, metadata ? JSON.stringify(metadata) : null],
    );
  }

  private async assertDemoQuota(userId: string): Promise<void> {
    if (this.config.get<string>('DEMO_MODE') !== 'true') return;
    const maximum = Number(this.config.get<string>('DEMO_MAX_SOURCES_PER_USER', '3'));
    const current = await this.resources.count({ where: { createdUserId: userId, isDeleted: false } });
    if (current >= maximum) {
      throw new ForbiddenException(
        `La demostración gratuita permite un máximo de ${maximum} fuentes nuevas por cuenta`,
      );
    }
  }

  private async project(id: string, user?: { id: string; role: string }) {
    const project = await this.projects.findOne({ where: { id, isDeleted: false } });
    if (!project) throw new NotFoundException('Proyecto no encontrado');
    if (user && user.role !== 'admin') {
      const memberships = await this.dataSource.query(
        `SELECT 1 FROM tfm_schema.project_memberships WHERE project_id = $1 AND user_id = $2`,
        [id, user.id],
      );
      if (!memberships.length) throw new ForbiddenException('No tienes acceso a este proyecto');
    }
    return project;
  }

  private async assertSegmentAccess(segmentId: string, userId: string) {
    const rows = await this.dataSource.query(
      `SELECT 1 FROM tfm_schema.resource_segments s
       JOIN tfm_schema.resources r ON r.id = s.resource_id
       JOIN tfm_schema.project_memberships pm ON pm.project_id = r.project_id
       WHERE s.id = $1 AND s.is_deleted = false AND pm.user_id = $2`,
      [segmentId, userId],
    );
    if (!rows.length) throw new ForbiddenException('No tienes acceso a este fragmento');
  }
}
