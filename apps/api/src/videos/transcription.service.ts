import { Inject, Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import {
  ML_SERVICE_PORT,
  MlServicePort,
  MlTranscriptResult,
  MlTranscriptUnavailable,
} from '../ml/ml-service.port';
import { SegmentEntity } from './entities/segment.entity';
import { TranscriptEntity } from './entities/transcript.entity';
import { VideoEntity } from './entities/video.entity';

/**
 * Orquesta la transcripción end-to-end (cascada + segmentación) y espeja el
 * estado en `videos.transcription_status`. Corre en segundo plano (in-process):
 * el controller lanza `run()` sin await y el front hace polling del estado.
 */
@Injectable()
export class TranscriptionService {
  private readonly logger = new Logger(TranscriptionService.name);

  constructor(
    @InjectRepository(VideoEntity) private readonly videos: Repository<VideoEntity>,
    @InjectRepository(TranscriptEntity) private readonly transcripts: Repository<TranscriptEntity>,
    @InjectRepository(SegmentEntity) private readonly segments: Repository<SegmentEntity>,
    @Inject(ML_SERVICE_PORT) private readonly ml: MlServicePort,
  ) {}

  /** Marca el video como `processing`. El controller lo hace con await antes de responder 202. */
  async markProcessing(videoId: string, userId: string): Promise<void> {
    await this.videos.update(videoId, { transcriptionStatus: 'processing', updatedUserId: userId });
  }

  /** Ejecuta la cascada de transcripción y segmentación para un video. */
  async run(videoId: string, userId: string): Promise<void> {
    const video = await this.videos.findOne({ where: { id: videoId, isDeleted: false } });
    if (!video) return;

    try {
      // 1) Cascada: subtítulos → fallback Whisper.
      let result: MlTranscriptResult;
      try {
        result = await this.ml.transcribeSubtitles(video.url);
      } catch (err) {
        if (err instanceof MlTranscriptUnavailable) {
          this.logger.warn(`Sin subtítulos para ${video.youtubeId} → fallback Whisper`);
          result = await this.ml.transcribeAudio(video.url);
        } else {
          throw err;
        }
      }

      // 2) Reemplaza transcripción/segmentos previos (re-transcripción idempotente).
      await this.softDeletePrevious(videoId, userId);

      const transcript = await this.transcripts.save(
        this.transcripts.create({
          videoId,
          language: result.language,
          source: result.source,
          isGenerated: result.is_generated,
          fullText: result.full_text,
          createdUserId: userId,
          updatedUserId: userId,
        }),
      );

      // 3) Segmentación por ventanas.
      const seg = await this.ml.segment(result.cues);
      if (seg.segments.length) {
        await this.segments.save(
          seg.segments.map((s) =>
            this.segments.create({
              videoId,
              transcriptId: transcript.id,
              idx: s.idx,
              startSec: s.start_sec,
              endSec: s.end_sec,
              text: s.text,
              createdUserId: userId,
              updatedUserId: userId,
            }),
          ),
        );
      }

      await this.videos.update(videoId, {
        transcriptionStatus: 'done',
        updatedUserId: userId,
      });
      this.logger.log(`Transcripción OK ${video.youtubeId}: ${seg.segments.length} segmentos (${result.source})`);
    } catch (err) {
      this.logger.error(`Transcripción falló para ${video.youtubeId}: ${(err as Error).message}`);
      await this.videos.update(videoId, { transcriptionStatus: 'failed', updatedUserId: userId });
    }
  }

  private async softDeletePrevious(videoId: string, userId: string): Promise<void> {
    const patch = { isDeleted: true, deletedAt: new Date(), deletedUserId: userId };
    await this.segments.update({ videoId, isDeleted: false }, patch);
    await this.transcripts.update({ videoId, isDeleted: false }, patch);
  }
}
