import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { LabelsModule } from '../labels/labels.module';
import { SegmentEntity } from '../videos/entities/segment.entity';
import { DatasetsController, ProjectDatasetsController, ValidationCampaignsController } from './datasets.controller';
import { DatasetsService } from './datasets.service';
import { DatasetItemEntity } from './entities/dataset-item.entity';
import { DatasetEntity } from './entities/dataset.entity';
import { ResourceSegmentEntity } from '../resources/entities/resource-segment.entity';

@Module({
  imports: [TypeOrmModule.forFeature([DatasetEntity, DatasetItemEntity, SegmentEntity, ResourceSegmentEntity]), LabelsModule],
  controllers: [DatasetsController, ProjectDatasetsController, ValidationCampaignsController],
  providers: [DatasetsService],
  exports: [DatasetsService],
})
export class DatasetsModule {}
