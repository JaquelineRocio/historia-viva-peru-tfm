import { SegmentEntity } from './entities/segment.entity';
import { TranscriptEntity } from './entities/transcript.entity';
import { VideoEntity } from './entities/video.entity';
import { SegmentResponseDto, TranscriptResponseDto, VideoResponseDto } from './dto/video-response.dto';

/** Nunca exponemos entidades TypeORM: mapeamos a DTO. */
export const VideosMapper = {
  toVideo(e: VideoEntity): VideoResponseDto {
    return {
      id: e.id,
      youtubeId: e.youtubeId,
      url: e.url,
      title: e.title,
      channel: e.channel,
      durationSec: e.durationSec,
      transcriptionStatus: e.transcriptionStatus,
      createdAt: e.createdAt,
    };
  },

  toSegment(e: SegmentEntity): SegmentResponseDto {
    return { id: e.id, idx: e.idx, startSec: e.startSec, endSec: e.endSec, text: e.text };
  },

  toTranscript(t: TranscriptEntity, segments: SegmentEntity[]): TranscriptResponseDto {
    return {
      id: t.id,
      videoId: t.videoId,
      language: t.language,
      source: t.source,
      isGenerated: t.isGenerated,
      segments: segments.map((s) => VideosMapper.toSegment(s)),
    };
  },
};
