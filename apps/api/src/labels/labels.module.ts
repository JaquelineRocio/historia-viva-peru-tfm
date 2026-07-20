import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { SegmentEntity } from '../videos/entities/segment.entity';
import { LabelsTaxonomyEntity } from './entities/labels-taxonomy.entity';
import { SegmentLabelEntity } from './entities/segment-label.entity';
import { LabelsController } from './labels.controller';
import { LabelsService } from './labels.service';

@Module({
  imports: [TypeOrmModule.forFeature([LabelsTaxonomyEntity, SegmentLabelEntity, SegmentEntity])],
  controllers: [LabelsController],
  providers: [LabelsService],
  exports: [LabelsService],
})
export class LabelsModule {}
