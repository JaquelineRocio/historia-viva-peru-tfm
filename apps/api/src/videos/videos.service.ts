import { BadRequestException, ConflictException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { CreateVideoDto } from './dto/create-video.dto';
import { SegmentEntity } from './entities/segment.entity';
import { TranscriptEntity } from './entities/transcript.entity';
import { VideoEntity } from './entities/video.entity';
import { extractYoutubeId } from './youtube-id.util';

@Injectable()
export class VideosService {
  constructor(
    @InjectRepository(VideoEntity) private readonly videos: Repository<VideoEntity>,
    @InjectRepository(TranscriptEntity) private readonly transcripts: Repository<TranscriptEntity>,
    @InjectRepository(SegmentEntity) private readonly segments: Repository<SegmentEntity>,
  ) {}

  async create(dto: CreateVideoDto, userId: string): Promise<VideoEntity> {
    const youtubeId = extractYoutubeId(dto.url);
    if (!youtubeId) throw new BadRequestException('URL/ID de YouTube no válido');

    const existing = await this.videos.findOne({ where: { youtubeId, isDeleted: false } });
    if (existing) throw new ConflictException('Ese video ya fue ingerido');

    return this.videos.save(
      this.videos.create({
        youtubeId,
        url: dto.url.trim(),
        title: dto.title,
        channel: dto.channel,
        transcriptionStatus: 'pending',
        createdUserId: userId,
        updatedUserId: userId,
      }),
    );
  }

  async findAll(): Promise<VideoEntity[]> {
    return this.videos.find({ where: { isDeleted: false }, order: { createdAt: 'DESC' } });
  }

  async findOneOrFail(id: string): Promise<VideoEntity> {
    const video = await this.videos.findOne({ where: { id, isDeleted: false } });
    if (!video) throw new NotFoundException('Video no encontrado');
    return video;
  }

  /** Última transcripción activa del video + sus segmentos ordenados. */
  async getTranscript(videoId: string): Promise<{ transcript: TranscriptEntity; segments: SegmentEntity[] } | null> {
    const transcript = await this.transcripts.findOne({
      where: { videoId, isDeleted: false },
      order: { createdAt: 'DESC' },
    });
    if (!transcript) return null;
    const segments = await this.segments.find({
      where: { videoId, transcriptId: transcript.id, isDeleted: false },
      order: { idx: 'ASC' },
    });
    return { transcript, segments };
  }

  async softDelete(id: string, userId: string): Promise<void> {
    const video = await this.findOneOrFail(id);
    const patch = { isDeleted: true, deletedAt: new Date(), deletedUserId: userId };
    await this.segments.update({ videoId: video.id, isDeleted: false }, patch);
    await this.transcripts.update({ videoId: video.id, isDeleted: false }, patch);
    await this.videos.update(video.id, patch);
  }
}
