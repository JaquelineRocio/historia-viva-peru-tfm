import { BadRequestException, ConflictException, ForbiddenException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { DataSource, In, Repository } from 'typeorm';
import { LabelsService } from '../labels/labels.service';
import { SegmentEntity } from '../videos/entities/segment.entity';
import { ResourceSegmentEntity } from '../resources/entities/resource-segment.entity';
import { CreateDatasetDto } from './dto/create-dataset.dto';
import { DatasetItemEntity } from './entities/dataset-item.entity';
import { DatasetEntity } from './entities/dataset.entity';
import { groupedSplit } from './split.util';

export function computeCohenKappa(pairs: Array<{ primary: string; secondary: string; count: number }>) {
  const completed = pairs.reduce((sum, pair) => sum + pair.count, 0);
  const observed = completed
    ? pairs.filter((pair) => pair.primary === pair.secondary).reduce((sum, pair) => sum + pair.count, 0) / completed
    : 0;
  const primary = new Map<string, number>();
  const secondary = new Map<string, number>();
  for (const pair of pairs) {
    primary.set(pair.primary, (primary.get(pair.primary) ?? 0) + pair.count);
    secondary.set(pair.secondary, (secondary.get(pair.secondary) ?? 0) + pair.count);
  }
  const expected = completed
    ? [...new Set([...primary.keys(), ...secondary.keys()])].reduce(
        (sum, key) => sum + ((primary.get(key) ?? 0) / completed) * ((secondary.get(key) ?? 0) / completed),
        0,
      )
    : 0;
  return { observed, expected, kappa: completed && expected < 1 ? (observed - expected) / (1 - expected) : null };
}

@Injectable()
export class DatasetsService {
  constructor(
    @InjectRepository(DatasetEntity) private readonly datasets: Repository<DatasetEntity>,
    @InjectRepository(DatasetItemEntity) private readonly items: Repository<DatasetItemEntity>,
    @InjectRepository(SegmentEntity) private readonly segments: Repository<SegmentEntity>,
    @InjectRepository(ResourceSegmentEntity) private readonly resourceSegments: Repository<ResourceSegmentEntity>,
    private readonly labels: LabelsService,
    private readonly dataSource: DataSource,
  ) {}

  async assertProjectAccess(projectId: string, user: { id: string; role: string }) {
    if (user.role === 'admin') return;
    const rows = await this.dataSource.query(
      `SELECT 1 FROM tfm_schema.project_memberships WHERE project_id = $1 AND user_id = $2`,
      [projectId, user.id],
    );
    if (!rows.length) throw new ForbiddenException('No tienes acceso a este proyecto');
  }

  async createAnnotationCampaign(
    projectId: string,
    dto: { name?: string; targetCount?: number; seed?: number; maxPerSource?: number },
    user: { id: string; role: string },
  ) {
    await this.assertProjectAccess(projectId, user);
    if (!['curador', 'admin'].includes(user.role)) {
      throw new ForbiddenException('Solo un curador puede crear la campaña gold');
    }
    const existing = await this.dataSource.query(
      `SELECT id FROM tfm_schema.primary_annotation_campaigns WHERE project_id = $1 AND status = 'open'`,
      [projectId],
    );
    if (existing.length) throw new ConflictException('Ya existe una campaña primaria abierta en este proyecto');
    const targetCount = dto.targetCount ?? 700;
    const seed = dto.seed ?? 42;
    const maxPerSource = dto.maxPerSource ?? 150;
    return this.dataSource.transaction(async (manager) => {
      const campaigns = await manager.query(
        `INSERT INTO tfm_schema.primary_annotation_campaigns
           (project_id, name, target_count, seed, max_per_source, created_user_id)
         VALUES ($1, $2, $3, $4, $5, $6)
         RETURNING id, project_id AS "projectId", name, target_count AS "targetCount",
                   seed, max_per_source AS "maxPerSource", status, created_at AS "createdAt"`,
        [projectId, dto.name || 'Corpus gold v1', targetCount, seed, maxPerSource, user.id],
      );
      const campaign = campaigns[0];
      const inserted = await manager.query(
        `WITH candidates AS (
           SELECT s.id,
                  row_number() OVER (
                    PARTITION BY r.id ORDER BY md5(s.id::text || $3::text)
                  ) AS source_rank
           FROM tfm_schema.resource_segments s
           JOIN tfm_schema.resources r ON r.id = s.resource_id
           WHERE r.project_id = $1 AND r.is_deleted = false
             AND r.corpus_status = 'included' AND r.processing_status = 'ready'
             AND s.is_deleted = false AND s.review_status IN ('pending', 'reviewed')
         ), eligible AS (
           SELECT id, source_rank,
                  row_number() OVER (ORDER BY source_rank, md5(id::text || $3::text)) AS position
           FROM candidates WHERE source_rank <= $4
         )
         INSERT INTO tfm_schema.primary_annotation_samples
           (campaign_id, resource_segment_id, position)
         SELECT $2, id, position FROM eligible WHERE position <= $5
         RETURNING id`,
        [projectId, campaign.id, seed, maxPerSource, targetCount],
      );
      if (inserted.length < targetCount) {
        throw new BadRequestException(
          `Solo hay ${inserted.length} candidatos con el límite de ${maxPerSource} por fuente; reduce el objetivo o amplía el corpus`,
        );
      }
      return { ...campaign, sampleCount: inserted.length, completedCount: 0 };
    });
  }

  async listAnnotationCampaigns(projectId: string, user: { id: string; role: string }) {
    await this.assertProjectAccess(projectId, user);
    return this.dataSource.query(
      `SELECT c.id, c.project_id AS "projectId", c.name,
              c.target_count AS "targetCount", c.seed,
              c.max_per_source AS "maxPerSource", c.status,
              c.created_at AS "createdAt",
              count(ps.id)::int AS "sampleCount",
              count(ps.id) FILTER (WHERE s.review_status = 'reviewed')::int AS "completedCount",
              count(DISTINCT s.resource_id)::int AS "sourceCount"
       FROM tfm_schema.primary_annotation_campaigns c
       LEFT JOIN tfm_schema.primary_annotation_samples ps ON ps.campaign_id = c.id
       LEFT JOIN tfm_schema.resource_segments s ON s.id = ps.resource_segment_id
       WHERE c.project_id = $1
       GROUP BY c.id ORDER BY c.created_at DESC`,
      [projectId],
    );
  }

  async annotationCampaignProgress(campaignId: string, user: { id: string; role: string }) {
    const campaigns = await this.dataSource.query(
      `SELECT id, project_id AS "projectId", name, target_count AS "targetCount",
              seed, max_per_source AS "maxPerSource", status
       FROM tfm_schema.primary_annotation_campaigns WHERE id = $1`,
      [campaignId],
    );
    if (!campaigns.length) throw new NotFoundException('Campaña primaria no encontrada');
    await this.assertProjectAccess(campaigns[0].projectId, user);
    const [totals, sources, classes] = await Promise.all([
      this.dataSource.query(
        `SELECT count(*)::int AS total,
                count(*) FILTER (WHERE s.review_status = 'pending')::int AS pending,
                count(*) FILTER (WHERE s.review_status = 'reviewed')::int AS reviewed,
                count(*) FILTER (WHERE s.review_status = 'ambiguous')::int AS ambiguous,
                count(*) FILTER (WHERE s.review_status = 'excluded')::int AS excluded
         FROM tfm_schema.primary_annotation_samples ps
         JOIN tfm_schema.resource_segments s ON s.id = ps.resource_segment_id
         WHERE ps.campaign_id = $1`,
        [campaignId],
      ),
      this.dataSource.query(
        `SELECT r.id AS "resourceId", r.title, r.type,
                count(*)::int AS total,
                count(*) FILTER (WHERE s.review_status = 'pending')::int AS pending,
                count(*) FILTER (WHERE s.review_status = 'reviewed')::int AS reviewed,
                count(*) FILTER (WHERE s.review_status = 'ambiguous')::int AS ambiguous,
                count(*) FILTER (WHERE s.review_status = 'excluded')::int AS excluded
         FROM tfm_schema.primary_annotation_samples ps
         JOIN tfm_schema.resource_segments s ON s.id = ps.resource_segment_id
         JOIN tfm_schema.resources r ON r.id = s.resource_id
         WHERE ps.campaign_id = $1
         GROUP BY r.id, r.title, r.type
         ORDER BY (count(*) FILTER (WHERE s.review_status = 'pending')) DESC, r.title`,
        [campaignId],
      ),
      this.dataSource.query(
        `SELECT t.key, t.name, t.color,
                count(s.id) FILTER (
                  WHERE s.review_status = 'reviewed' AND s.reviewed_label_key = t.key
                )::int AS count
         FROM tfm_schema.labels_taxonomy t
         LEFT JOIN tfm_schema.primary_annotation_samples ps ON ps.campaign_id = $1
         LEFT JOIN tfm_schema.resource_segments s ON s.id = ps.resource_segment_id
         WHERE t.is_deleted = false
         GROUP BY t.key, t.name, t.color, t.sort_order
         ORDER BY t.sort_order`,
        [campaignId],
      ),
    ]);
    return {
      campaign: campaigns[0],
      totals: totals[0],
      sources,
      classes: classes.map((item: { key: string; name: string; color: string; count: number }) => ({
        ...item,
        target: 100,
        missing: Math.max(0, 100 - item.count),
      })),
    };
  }

  async createValidationCampaign(
    projectId: string,
    dto: { name?: string; sampleRate?: number; seed?: number },
    user: { id: string; role: string },
  ) {
    await this.assertProjectAccess(projectId, user);
    const sampleRate = dto.sampleRate ?? 0.2;
    const seed = dto.seed ?? 42;
    return this.dataSource.transaction(async (manager) => {
      const campaigns = await manager.query(
        `INSERT INTO tfm_schema.annotation_validation_campaigns
           (project_id, name, sample_rate, seed, created_user_id)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING id, project_id AS "projectId", name, sample_rate::float AS "sampleRate",
                   seed, status, created_at AS "createdAt"`,
        [projectId, dto.name || `Segunda revision ${new Date().toISOString().slice(0, 10)}`, sampleRate, seed, user.id],
      );
      const campaign = campaigns[0];
      const inserted = await manager.query(
        `WITH ranked AS (
           SELECT s.id, s.reviewed_label_key, s.reviewed_user_id,
                  row_number() OVER (
                    PARTITION BY s.reviewed_label_key
                    ORDER BY md5(s.id::text || $3::text)
                  ) AS position,
                  count(*) OVER (PARTITION BY s.reviewed_label_key) AS class_total
           FROM tfm_schema.resource_segments s
           JOIN tfm_schema.resources r ON r.id = s.resource_id
           WHERE r.project_id = $1 AND r.is_deleted = false AND r.corpus_status = 'included'
             AND s.is_deleted = false AND s.review_status = 'reviewed'
             AND s.reviewed_label_key IS NOT NULL
         )
         INSERT INTO tfm_schema.annotation_validation_samples
           (campaign_id, resource_segment_id, primary_label_key, primary_user_id)
         SELECT $2, id, reviewed_label_key, reviewed_user_id
         FROM ranked
         WHERE position <= greatest(1, ceil(class_total * $4::numeric)::int)
         RETURNING id`,
        [projectId, campaign.id, seed, sampleRate],
      );
      if (!inserted.length) throw new BadRequestException('Primero debes revisar segmentos antes de crear la muestra del 20%');
      return { ...campaign, sampleCount: inserted.length, completedCount: 0 };
    });
  }

  async listValidationCampaigns(projectId: string, user: { id: string; role: string }) {
    await this.assertProjectAccess(projectId, user);
    return this.dataSource.query(
      `SELECT c.id, c.project_id AS "projectId", c.name, c.sample_rate::float AS "sampleRate",
              c.seed, c.status, c.created_at AS "createdAt",
              count(s.id)::int AS "sampleCount",
              count(s.secondary_label_key)::int AS "completedCount"
       FROM tfm_schema.annotation_validation_campaigns c
       LEFT JOIN tfm_schema.annotation_validation_samples s ON s.campaign_id = c.id
       WHERE c.project_id = $1
       GROUP BY c.id ORDER BY c.created_at DESC`,
      [projectId],
    );
  }

  async validationSamples(campaignId: string, page: number, limit: number, user: { id: string; role: string }) {
    const campaigns = await this.dataSource.query(
      `SELECT project_id AS "projectId" FROM tfm_schema.annotation_validation_campaigns WHERE id = $1`,
      [campaignId],
    );
    if (!campaigns.length) throw new NotFoundException('Campaña no encontrada');
    await this.assertProjectAccess(campaigns[0].projectId, user);
    const safePage = Math.max(1, page || 1);
    const safeLimit = Math.min(100, Math.max(1, limit || 25));
    const rows = await this.dataSource.query(
      `SELECT vs.id, vs.resource_segment_id AS "segmentId", vs.secondary_label_key AS "secondaryLabelKey",
              vs.reviewed_at AS "reviewedAt", s.text, s.locator_type AS "locatorType",
              s.start_sec AS "startSec", s.end_sec AS "endSec", s.page_start AS "pageStart",
              s.page_end AS "pageEnd", r.title AS "resourceTitle", r.type AS "resourceType"
       FROM tfm_schema.annotation_validation_samples vs
       JOIN tfm_schema.resource_segments s ON s.id = vs.resource_segment_id
       JOIN tfm_schema.resources r ON r.id = s.resource_id
       WHERE vs.campaign_id = $1
       ORDER BY (vs.secondary_label_key IS NOT NULL), md5(vs.id::text)
       LIMIT $2 OFFSET $3`,
      [campaignId, safeLimit, (safePage - 1) * safeLimit],
    );
    const count = await this.dataSource.query(
      `SELECT count(*)::int AS total FROM tfm_schema.annotation_validation_samples WHERE campaign_id = $1`,
      [campaignId],
    );
    const total = count[0].total;
    return { items: rows, page: safePage, limit: safeLimit, total, totalPages: Math.max(1, Math.ceil(total / safeLimit)) };
  }

  async saveSecondaryAnnotation(sampleId: string, labelKey: string, user: { id: string; role: string }) {
    const rows = await this.dataSource.query(
      `SELECT c.project_id AS "projectId", c.status, s.primary_user_id AS "primaryUserId"
       FROM tfm_schema.annotation_validation_samples s
       JOIN tfm_schema.annotation_validation_campaigns c ON c.id = s.campaign_id
       WHERE s.id = $1`,
      [sampleId],
    );
    if (!rows.length) throw new NotFoundException('Muestra no encontrada');
    await this.assertProjectAccess(rows[0].projectId, user);
    if (rows[0].status !== 'open') throw new BadRequestException('La campaña está cerrada');
    if (rows[0].primaryUserId === user.id) throw new ForbiddenException('La segunda revisión debe realizarla otra persona');
    const labels = await this.dataSource.query(
      `SELECT 1 FROM tfm_schema.labels_taxonomy WHERE key = $1 AND is_deleted = false`,
      [labelKey],
    );
    if (!labels.length) throw new BadRequestException('La etiqueta no pertenece a la taxonomía activa');
    await this.dataSource.query(
      `UPDATE tfm_schema.annotation_validation_samples
       SET secondary_label_key = $2, secondary_user_id = $3, reviewed_at = now()
       WHERE id = $1`,
      [sampleId, labelKey, user.id],
    );
    return { sampleId, labelKey, saved: true };
  }

  async validationAgreement(campaignId: string, user: { id: string; role: string }) {
    const campaigns = await this.dataSource.query(
      `SELECT project_id AS "projectId" FROM tfm_schema.annotation_validation_campaigns WHERE id = $1`,
      [campaignId],
    );
    if (!campaigns.length) throw new NotFoundException('Campaña no encontrada');
    await this.assertProjectAccess(campaigns[0].projectId, user);
    const pairs = await this.dataSource.query(
      `SELECT primary_label_key AS primary, secondary_label_key AS secondary, count(*)::int AS count
       FROM tfm_schema.annotation_validation_samples
       WHERE campaign_id = $1 AND secondary_label_key IS NOT NULL
       GROUP BY primary_label_key, secondary_label_key`,
      [campaignId],
    );
    const totals = await this.dataSource.query(
      `SELECT count(*)::int AS total, count(secondary_label_key)::int AS completed
       FROM tfm_schema.annotation_validation_samples WHERE campaign_id = $1`,
      [campaignId],
    );
    const completed = totals[0].completed as number;
    const agreement = computeCohenKappa(pairs);
    return { total: totals[0].total, completed, observedAgreement: agreement.observed, expectedAgreement: agreement.expected, kappa: agreement.kappa, targetMet: agreement.kappa !== null && agreement.kappa >= 0.7, confusion: pairs };
  }

  async readiness(projectId?: string) {
    if (projectId) {
      const distribution = await this.dataSource.query(
        `SELECT t.key, t.name, count(r.id)::int AS count
         FROM tfm_schema.labels_taxonomy t
         LEFT JOIN tfm_schema.resource_segments s
           ON s.reviewed_label_key = t.key AND s.is_deleted = false AND s.review_status = 'reviewed'
         LEFT JOIN tfm_schema.resources r ON r.id = s.resource_id AND r.project_id = $1 AND r.is_deleted = false AND r.corpus_status = 'included'
         WHERE t.is_deleted = false
         GROUP BY t.key, t.name, t.sort_order ORDER BY t.sort_order`,
        [projectId],
      );
      const targetPerClass = 100;
      const sourceStats = await this.dataSource.query(
        `SELECT count(*)::int AS total,
                count(*) FILTER (WHERE type = 'pdf')::int AS pdf,
                count(*) FILTER (WHERE type = 'youtube')::int AS youtube,
                count(*) FILTER (WHERE processing_status = 'ready')::int AS processed
         FROM tfm_schema.resources WHERE project_id = $1 AND is_deleted = false AND corpus_status = 'included'`,
        [projectId],
      );
      const goldSources = await this.dataSource.query(
        `SELECT count(DISTINCT r.id)::int AS total
         FROM tfm_schema.resources r JOIN tfm_schema.resource_segments s ON s.resource_id = r.id
         WHERE r.project_id = $1 AND r.is_deleted = false AND r.corpus_status = 'included' AND s.is_deleted = false
           AND s.review_status = 'reviewed'`,
        [projectId],
      );
      const total = distribution.reduce((sum: number, item: { count: number }) => sum + item.count, 0);
      const sources = { ...sourceStats[0], gold: goldSources[0].total, targetMin: 8, targetMax: 12 };
      return {
        targetPerClass,
        targetTotalMin: 700,
        targetTotalMax: 900,
        total,
        ready: total >= 700 && total <= 900 && sources.gold >= 8 && sources.pdf >= 1 && sources.youtube >= 1 && distribution.every((item: { count: number }) => item.count >= targetPerClass),
        sources,
        distribution,
      };
    }
    const distribution = await this.dataSource.query(
      `SELECT t.key, t.name, count(x.label_key)::int AS count
       FROM tfm_schema.labels_taxonomy t
       LEFT JOIN (
         SELECT label_key FROM tfm_schema.segment_labels WHERE is_deleted = false AND is_gold = true
         UNION ALL
         SELECT reviewed_label_key AS label_key FROM tfm_schema.resource_segments
         WHERE is_deleted = false AND review_status = 'reviewed' AND reviewed_label_key IS NOT NULL
       ) x ON x.label_key = t.key
       WHERE t.is_deleted = false
       GROUP BY t.key, t.name, t.sort_order
       ORDER BY t.sort_order`,
    );
    const targetPerClass = 30;
    return {
      targetPerClass,
      total: distribution.reduce((sum: number, item: { count: number }) => sum + item.count, 0),
      ready: distribution.length >= 2 && distribution.every((item: { count: number }) => item.count >= targetPerClass),
      distribution,
    };
  }

  /**
   * Crea un snapshot INMUTABLE del dataset a partir de las etiquetas gold
   * actuales: congela texto + label + split. Esto garantiza comparaciones
   * justas y reproducibles entre versiones del modelo.
   */
  async createSnapshot(dto: CreateDatasetDto, userId: string, projectId?: string): Promise<DatasetEntity> {
    const gold = await this.labels.getAllGold();
    const segIds = gold.map((g) => g.segmentId);
    const segs = await this.segments.find({ where: { id: In(segIds), isDeleted: false } });
    const textById = new Map(segs.map((s) => [s.id, s.text]));
    const videoById = new Map(segs.map((s) => [s.id, s.videoId]));

    // Los segmentos del sistema de videos anterior no pertenecen a un
    // proyecto. Solo se conservan en el endpoint legado `/datasets`; un
    // snapshot creado dentro de un proyecto debe contener exclusivamente
    // sus recursos y su taxonomía activa.
    const legacyRaw = (projectId ? [] : gold)
      .filter((g) => textById.has(g.segmentId))
      .map((g) => ({
        segmentId: g.segmentId,
        resourceSegmentId: null,
        label: g.labelKey,
        text: textById.get(g.segmentId)!,
        group: `video:${videoById.get(g.segmentId)}`,
        stratum: 'youtube',
      }));
    const projectResources: Array<{ id: string; type: string }> = projectId
      ? await this.dataSource.query(
          `SELECT id, type FROM tfm_schema.resources
           WHERE project_id = $1 AND is_deleted = false AND corpus_status = 'included'`,
          [projectId],
        )
      : [];
    const resourceIds = projectResources.map((row) => row.id);
    const resourceTypeById = new Map(projectResources.map((row) => [row.id, row.type]));
    const reviewed = await this.resourceSegments.find({
      where: projectId
        ? { resourceId: In(resourceIds), reviewStatus: 'reviewed', isDeleted: false }
        : { reviewStatus: 'reviewed', isDeleted: false },
    });
    const activeLabelKeys = projectId
      ? new Set<string>((await this.dataSource.query(
          `SELECT key FROM tfm_schema.labels_taxonomy WHERE is_deleted = false`,
        )).map((row: { key: string }) => row.key))
      : null;
    const resourceRaw = reviewed
      .filter((segment) => !!segment.reviewedLabelKey && (!activeLabelKeys || activeLabelKeys.has(segment.reviewedLabelKey!)))
      .map((segment) => ({
        segmentId: null,
        resourceSegmentId: segment.id,
        label: segment.reviewedLabelKey!,
        text: segment.text,
        group: `resource:${segment.resourceId}`,
        stratum: resourceTypeById.get(segment.resourceId),
      }));
    const raw = [...legacyRaw, ...resourceRaw];
    if (raw.length < 6) {
      throw new BadRequestException(`Muy pocos ejemplos revisados (${raw.length}). Revisa más fragmentos antes de crear un dataset.`);
    }

    const trainRatio = dto.trainRatio ?? 0.7;
    const valRatio = dto.valRatio ?? 0.15;
    const seed = dto.seed ?? 42;
    const split = groupedSplit(raw, trainRatio, valRatio, seed);

    const classDistribution: Record<string, number> = {};
    for (const it of raw) classDistribution[it.label] = (classDistribution[it.label] ?? 0) + 1;

    const dataset = await this.datasets.save(
      this.datasets.create({
        projectId: projectId ?? null,
        name: dto.name,
        description: dto.description,
        nSamples: raw.length,
        classDistribution,
        splitConfig: { trainRatio, valRatio, testRatio: +(1 - trainRatio - valRatio).toFixed(3), seed, groupedByResource: true },
        createdUserId: userId,
        updatedUserId: userId,
      }),
    );

    await this.items.save(
      split.map((s) =>
        this.items.create({
          datasetId: dataset.id,
          segmentId: s.segmentId,
          resourceSegmentId: s.resourceSegmentId,
          labelKey: s.label,
          text: s.text,
          split: s.split,
        }),
      ),
    );

    return dataset;
  }

  findAll(): Promise<DatasetEntity[]> {
    return this.datasets.find({ where: { isDeleted: false }, order: { createdAt: 'DESC' } });
  }

  findAllByProject(projectId: string): Promise<DatasetEntity[]> {
    return this.datasets.find({ where: { projectId, isDeleted: false }, order: { createdAt: 'DESC' } });
  }

  async findOneOrFail(id: string): Promise<DatasetEntity> {
    const d = await this.datasets.findOne({ where: { id, isDeleted: false } });
    if (!d) throw new NotFoundException('Dataset no encontrado');
    return d;
  }

  getItems(datasetId: string): Promise<DatasetItemEntity[]> {
    return this.items.find({ where: { datasetId } });
  }

  getExportItems(datasetId: string): Promise<Array<DatasetItemEntity & {
    resourceId: string | null;
    sourceType: string | null;
  }>> {
    return this.dataSource.query(
      `SELECT di.id, di.dataset_id AS "datasetId",
              di.segment_id AS "segmentId", di.resource_segment_id AS "resourceSegmentId",
              di.label_key AS "labelKey", di.text, di.split,
              rs.resource_id AS "resourceId", r.type AS "sourceType"
       FROM tfm_schema.dataset_items di
       LEFT JOIN tfm_schema.resource_segments rs ON rs.id = di.resource_segment_id
       LEFT JOIN tfm_schema.resources r ON r.id = rs.resource_id
       WHERE di.dataset_id = $1`,
      [datasetId],
    );
  }
}
