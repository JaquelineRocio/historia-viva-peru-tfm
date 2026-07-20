import { ModelVersionEntity } from './entities/model-version.entity';
import { TrainingJobEntity } from './entities/training-job.entity';
import { TrainingMetricEntity } from './entities/training-metric.entity';
import {
  ModelVersionResponseDto,
  TrainingJobResponseDto,
  TrainingMetricResponseDto,
} from './dto/training-response.dto';

/** Nunca exponemos entidades TypeORM: mapeamos a DTO. */
export const TrainingMapper = {
  toVersion(e: ModelVersionEntity): ModelVersionResponseDto {
    return {
      id: e.id,
      versionTag: e.versionTag,
      datasetId: e.datasetId,
      projectId: e.projectId,
      baseModel: e.baseModel,
      parentVersionId: e.parentVersionId,
      hyperparams: e.hyperparams,
      artifactPath: e.artifactPath,
      status: e.status,
      isActive: e.isActive,
      recommendationStatus: e.recommendationStatus,
      createdAt: e.createdAt,
    };
  },

  toJob(e: TrainingJobEntity): TrainingJobResponseDto {
    return {
      id: e.id,
      modelVersionId: e.modelVersionId,
      datasetId: e.datasetId,
      status: e.status,
      progress: e.progress,
      currentEpoch: e.currentEpoch,
      error: e.error,
      startedAt: e.startedAt,
      finishedAt: e.finishedAt,
      createdAt: e.createdAt,
    };
  },

  toMetric(e: TrainingMetricEntity): TrainingMetricResponseDto {
    return {
      id: e.id,
      modelVersionId: e.modelVersionId,
      split: e.split,
      accuracy: e.accuracy,
      precisionMacro: e.precisionMacro,
      recallMacro: e.recallMacro,
      f1Macro: e.f1Macro,
      f1Weighted: e.f1Weighted,
      f1MacroCi95: e.f1MacroCi95,
      resultsBySourceType: e.resultsBySourceType,
      baselineName: e.baselineName,
      baselineF1Macro: e.baselineF1Macro,
      baselineDatasetSha256: e.baselineDatasetSha256,
      exceedsBaseline: e.exceedsBaseline,
      perClassMetrics: e.perClassMetrics,
      confusionMatrix: e.confusionMatrix,
      createdAt: e.createdAt,
    };
  },
};
