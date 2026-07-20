import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { DatasetsModule } from '../datasets/datasets.module';
import { LabelsModule } from '../labels/labels.module';
import { MlModule } from '../ml/ml.module';
import { SegmentEntity } from '../videos/entities/segment.entity';
import { ModelVersionEntity } from './entities/model-version.entity';
import { TrainingJobEntity } from './entities/training-job.entity';
import { TrainingMetricEntity } from './entities/training-metric.entity';
import { InferenceService } from './inference.service';
import { TrainingController } from './training.controller';
import { TrainingService } from './training.service';

@Module({
  imports: [
    TypeOrmModule.forFeature([ModelVersionEntity, TrainingJobEntity, TrainingMetricEntity, SegmentEntity]),
    MlModule,
    DatasetsModule,
    LabelsModule,
  ],
  controllers: [TrainingController],
  providers: [TrainingService, InferenceService],
  exports: [TrainingService],
})
export class TrainingModule {}
