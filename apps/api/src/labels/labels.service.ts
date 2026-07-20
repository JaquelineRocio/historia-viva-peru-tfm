import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { EntityManager, In, Repository } from 'typeorm';
import { SegmentEntity } from '../videos/entities/segment.entity';
import { LabelsTaxonomyEntity } from './entities/labels-taxonomy.entity';
import { LabelSource, SegmentLabelEntity } from './entities/segment-label.entity';

export interface SegmentLabelView {
  labelKey: string;
  source: LabelSource;
  confidence?: number | null;
  isGold: boolean;
}

@Injectable()
export class LabelsService {
  constructor(
    @InjectRepository(LabelsTaxonomyEntity) private readonly taxonomy: Repository<LabelsTaxonomyEntity>,
    @InjectRepository(SegmentLabelEntity) private readonly labels: Repository<SegmentLabelEntity>,
    @InjectRepository(SegmentEntity) private readonly segments: Repository<SegmentEntity>,
  ) {}

  getTaxonomy(): Promise<LabelsTaxonomyEntity[]> {
    return this.taxonomy.find({ where: { isDeleted: false }, order: { sortOrder: 'ASC' } });
  }

  /**
   * Etiqueta activa por segmento (una sola, por el índice único). Soft-delete +
   * insert van en la misma transacción para no violar el índice ni dejar el
   * segmento transitoriamente sin etiqueta bajo concurrencia.
   */
  private replaceActiveLabel(
    segmentId: string,
    labelKey: string,
    source: LabelSource,
    userId: string,
    opts?: { confidence?: number | null; isGold?: boolean },
  ): Promise<SegmentLabelEntity> {
    return this.labels.manager.transaction((em) => this.replaceActiveLabelWith(em, segmentId, labelKey, source, userId, opts));
  }

  private async replaceActiveLabelWith(
    em: EntityManager,
    segmentId: string,
    labelKey: string,
    source: LabelSource,
    userId: string,
    opts?: { confidence?: number | null; isGold?: boolean },
  ): Promise<SegmentLabelEntity> {
    await em.update(
      SegmentLabelEntity,
      { segmentId, isDeleted: false },
      { isDeleted: true, deletedAt: new Date(), deletedUserId: userId },
    );
    return em.save(
      em.create(SegmentLabelEntity, {
        segmentId,
        labelKey,
        source,
        confidence: opts?.confidence ?? null,
        isGold: opts?.isGold ?? source === 'human',
        createdUserId: userId,
        updatedUserId: userId,
      }),
    );
  }

  /** Etiquetado humano (gold) de un segmento. */
  setHuman(segmentId: string, labelKey: string, userId: string): Promise<SegmentLabelEntity> {
    return this.replaceActiveLabel(segmentId, labelKey, 'human', userId, { isGold: true });
  }

  /** Etiquetado humano masivo — atómico: o se aplican todas o ninguna. */
  async bulkSetHuman(segmentIds: string[], labelKey: string, userId: string): Promise<number> {
    await this.labels.manager.transaction(async (em) => {
      for (const id of segmentIds) {
        await this.replaceActiveLabelWith(em, id, labelKey, 'human', userId, { isGold: true });
      }
    });
    return segmentIds.length;
  }

  /** Guarda una predicción del modelo (source=model, no gold). Usado por inferencia. */
  savePrediction(segmentId: string, labelKey: string, confidence: number, userId: string): Promise<SegmentLabelEntity> {
    return this.replaceActiveLabel(segmentId, labelKey, 'model', userId, { confidence, isGold: false });
  }

  /** Mapa segmentId → etiqueta activa, para un conjunto de segmentos. */
  async getLabelsForSegments(segmentIds: string[]): Promise<Record<string, SegmentLabelView>> {
    if (!segmentIds.length) return {};
    const rows = await this.labels.find({ where: { segmentId: In(segmentIds), isDeleted: false } });
    const map: Record<string, SegmentLabelView> = {};
    for (const r of rows) {
      map[r.segmentId] = { labelKey: r.labelKey, source: r.source, confidence: r.confidence, isGold: r.isGold };
    }
    return map;
  }

  /** Mapa de etiquetas activas de todos los segmentos de un video. */
  async getLabelsForVideo(videoId: string): Promise<Record<string, SegmentLabelView>> {
    const segs = await this.segments.find({ where: { videoId, isDeleted: false }, select: { id: true } });
    return this.getLabelsForSegments(segs.map((s) => s.id));
  }

  /** Todas las etiquetas gold (para construir datasets). */
  getAllGold(): Promise<SegmentLabelEntity[]> {
    return this.labels.find({ where: { isDeleted: false, isGold: true } });
  }
}
