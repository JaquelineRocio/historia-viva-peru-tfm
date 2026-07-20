import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { ModelStatus } from '../entities/model-version.entity';
import { JobStatus } from '../entities/training-job.entity';

export class ModelVersionResponseDto {
  @ApiProperty() id!: string;
  @ApiProperty() versionTag!: string;
  @ApiPropertyOptional() datasetId?: string | null;
  @ApiPropertyOptional() projectId?: string | null;
  @ApiProperty() baseModel!: string;
  @ApiPropertyOptional() parentVersionId?: string | null;
  @ApiPropertyOptional() hyperparams?: Record<string, unknown> | null;
  @ApiPropertyOptional() artifactPath?: string | null;
  @ApiProperty({ enum: ['training', 'ready', 'failed'] }) status!: ModelStatus;
  @ApiProperty() isActive!: boolean;
  @ApiProperty({ enum: ['experimental', 'recommended'] }) recommendationStatus!: string;
  @ApiProperty() createdAt!: Date;
}

export class TrainingJobResponseDto {
  @ApiProperty() id!: string;
  @ApiPropertyOptional() modelVersionId?: string | null;
  @ApiPropertyOptional() datasetId?: string | null;
  @ApiProperty({ enum: ['queued', 'running', 'done', 'failed', 'cancelled'] }) status!: JobStatus;
  @ApiProperty() progress!: number;
  @ApiPropertyOptional() currentEpoch?: number | null;
  @ApiPropertyOptional() error?: string | null;
  @ApiPropertyOptional() startedAt?: Date | null;
  @ApiPropertyOptional() finishedAt?: Date | null;
  @ApiProperty() createdAt!: Date;
}

export class TrainingMetricResponseDto {
  @ApiProperty() id!: string;
  @ApiProperty() modelVersionId!: string;
  @ApiProperty() split!: string;
  @ApiPropertyOptional() accuracy?: number | null;
  @ApiPropertyOptional() precisionMacro?: number | null;
  @ApiPropertyOptional() recallMacro?: number | null;
  @ApiPropertyOptional() f1Macro?: number | null;
  @ApiPropertyOptional() f1Weighted?: number | null;
  @ApiPropertyOptional() f1MacroCi95?: unknown;
  @ApiPropertyOptional() resultsBySourceType?: unknown;
  @ApiPropertyOptional() baselineName?: string | null;
  @ApiPropertyOptional() baselineF1Macro?: number | null;
  @ApiPropertyOptional() baselineDatasetSha256?: string | null;
  @ApiPropertyOptional() exceedsBaseline?: boolean | null;
  @ApiPropertyOptional() perClassMetrics?: unknown;
  @ApiPropertyOptional() confusionMatrix?: unknown;
  @ApiProperty() createdAt!: Date;
}
