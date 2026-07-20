import { BadRequestException, Inject, Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { LabelsService } from '../labels/labels.service';
import { ML_SERVICE_PORT, MlServicePort } from '../ml/ml-service.port';
import { SegmentEntity } from '../videos/entities/segment.entity';
import { TrainingService } from './training.service';

export interface SegmentPrediction {
  segmentId: string;
  idx: number;
  startSec: number;
  endSec: number;
  text: string;
  labelKey: string;
  confidence: number;
}

@Injectable()
export class InferenceService {
  constructor(
    @InjectRepository(SegmentEntity) private readonly segments: Repository<SegmentEntity>,
    @Inject(ML_SERVICE_PORT) private readonly ml: MlServicePort,
    private readonly labels: LabelsService,
    private readonly training: TrainingService,
  ) {}

  /**
   * Clasifica todos los segmentos de un video con el modelo activo y GUARDA las
   * predicciones (source=model). Base del active learning: la docente corrige y
   * esas correcciones (gold) alimentan el próximo dataset.
   */
  async classifyVideo(videoId: string, userId: string): Promise<SegmentPrediction[]> {
    await this.ensureActiveModel();
    const segs = await this.segments.find({
      where: { videoId, isDeleted: false },
      order: { idx: 'ASC' },
    });
    if (!segs.length) throw new BadRequestException('El video no tiene segmentos (transcríbelo primero)');

    const preds = await this.ml.infer(segs.map((s) => s.text));
    const out: SegmentPrediction[] = [];
    for (let i = 0; i < segs.length; i++) {
      const s = segs[i];
      const p = preds[i];
      if (!p) continue;
      await this.labels.savePrediction(s.id, p.label, p.confidence, userId);
      out.push({
        segmentId: s.id,
        idx: s.idx,
        startSec: s.startSec,
        endSec: s.endSec,
        text: s.text,
        labelKey: p.label,
        confidence: p.confidence,
      });
    }
    return out;
  }

  private async ensureActiveModel(): Promise<void> {
    const active = await this.training.getActive();
    if (!active) throw new BadRequestException('No hay modelo activo. Entrena y activa una versión primero.');
  }
}
