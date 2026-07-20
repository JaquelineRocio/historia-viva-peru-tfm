import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { MlModule } from '../ml/ml.module';
import { SegmentEntity } from './entities/segment.entity';
import { TranscriptEntity } from './entities/transcript.entity';
import { VideoEntity } from './entities/video.entity';
import { TranscriptionService } from './transcription.service';
import { VideosController } from './videos.controller';
import { VideosService } from './videos.service';

@Module({
  imports: [TypeOrmModule.forFeature([VideoEntity, TranscriptEntity, SegmentEntity]), MlModule],
  controllers: [VideosController],
  providers: [VideosService, TranscriptionService],
  exports: [VideosService],
})
export class VideosModule {}
