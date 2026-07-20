import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import {
  IsArray,
  IsInt,
  IsNumber,
  IsOptional,
  IsString,
  IsUUID,
  Max,
  MaxLength,
  Min,
  ValidateNested,
} from 'class-validator';

export class HyperparamsDto {
  @ApiPropertyOptional({ default: 4 })
  @IsOptional() @IsInt() @Min(1) @Max(10)
  epochs?: number;

  @ApiPropertyOptional({ default: 0.00002 })
  @IsOptional() @IsNumber()
  lr?: number;

  @ApiPropertyOptional({ default: 8 })
  @IsOptional() @IsInt() @Min(2) @Max(64)
  batch_size?: number;

  @ApiPropertyOptional({ default: 192 })
  @IsOptional() @IsInt() @Min(64) @Max(512)
  max_len?: number;

  @ApiPropertyOptional({ default: 42 })
  @IsOptional() @IsInt()
  seed?: number;
}

/** Métrica por clase tal como la produce el trainer (mismo shape que MlPerClassMetric). */
export class ImportedPerClassMetricDto {
  @ApiProperty() @IsString() label!: string;
  @ApiProperty() @IsNumber() precision!: number;
  @ApiProperty() @IsNumber() recall!: number;
  @ApiProperty() @IsNumber() f1!: number;
  @ApiProperty() @IsInt() support!: number;
}

export class ImportedConfidenceIntervalDto {
  @ApiProperty() @IsString() method!: string;
  @ApiProperty() @IsInt() @Min(1) iterations!: number;
  @ApiProperty() @IsInt() seed!: number;
  @ApiProperty() @IsNumber() low!: number;
  @ApiProperty() @IsNumber() high!: number;
}

export class ImportedBaselineDto {
  @ApiProperty({ example: 'tfidf_logistic_regression' })
  @IsString() name!: string;

  @ApiProperty({ description: 'F1 macro del baseline sobre el mismo test' })
  @IsNumber() f1_macro!: number;

  @ApiPropertyOptional({ description: 'SHA-256 de la exportación inmutable evaluada' })
  @IsOptional() @IsString()
  dataset_sha256?: string;
}

/** Métricas de un entrenamiento externo (Colab/Kaggle), mismo shape que MlMetrics. */
export class ImportedMetricsDto {
  @ApiProperty() @IsNumber() accuracy!: number;
  @ApiProperty() @IsNumber() precision_macro!: number;
  @ApiProperty() @IsNumber() recall_macro!: number;
  @ApiProperty() @IsNumber() f1_macro!: number;

  @ApiPropertyOptional() @IsOptional() @IsNumber()
  f1_weighted?: number;

  @ApiProperty({ type: [ImportedPerClassMetricDto] })
  @IsArray() @ValidateNested({ each: true }) @Type(() => ImportedPerClassMetricDto)
  per_class!: ImportedPerClassMetricDto[];

  @ApiProperty({ type: 'array', items: { type: 'array', items: { type: 'number' } } })
  @IsArray()
  confusion_matrix!: number[][];

  @ApiProperty({ type: [String] })
  @IsArray() @IsString({ each: true })
  labels!: string[];

  @ApiPropertyOptional({ description: 'Split sobre el que se calcularon (test|val|train)', default: 'test' })
  @IsOptional() @IsString()
  split?: string;

  @ApiPropertyOptional({ type: ImportedConfidenceIntervalDto })
  @IsOptional() @ValidateNested() @Type(() => ImportedConfidenceIntervalDto)
  f1_macro_ci95?: ImportedConfidenceIntervalDto;

  @ApiPropertyOptional({ type: 'object', additionalProperties: true })
  @IsOptional()
  results_by_source_type?: Record<string, unknown>;

  @ApiPropertyOptional({ type: ImportedBaselineDto })
  @IsOptional() @ValidateNested() @Type(() => ImportedBaselineDto)
  baseline?: ImportedBaselineDto;
}

/** Registro de una versión entrenada fuera del sistema (Colab/Kaggle). */
export class ImportModelDto {
  @ApiProperty({ description: 'Ruta del artefacto en el servicio ML, p. ej. storage/models/v2' })
  @IsString() @MaxLength(400)
  artifactPath!: string;

  @ApiPropertyOptional({ description: 'Etiqueta de versión (auto si se omite: v1, v2, …)' })
  @IsOptional() @IsString() @MaxLength(30)
  versionTag?: string;

  @ApiPropertyOptional({ description: 'Dataset con el que se entrenó (si existe en la BD)' })
  @IsOptional() @IsUUID()
  datasetId?: string;

  @ApiPropertyOptional({ description: 'Versión padre para linaje (fine-tuning incremental)' })
  @IsOptional() @IsUUID()
  parentVersionId?: string;

  @ApiPropertyOptional({ type: HyperparamsDto })
  @IsOptional() @ValidateNested() @Type(() => HyperparamsDto)
  hyperparams?: HyperparamsDto;

  @ApiPropertyOptional({ type: ImportedMetricsDto, description: 'Métricas para comparar en Versiones' })
  @IsOptional() @ValidateNested() @Type(() => ImportedMetricsDto)
  metrics?: ImportedMetricsDto;
}

export class CreateTrainingJobDto {
  @ApiProperty()
  @IsUUID()
  datasetId!: string;

  @ApiPropertyOptional({ description: 'Versión padre para fine-tuning incremental' })
  @IsOptional() @IsUUID()
  parentVersionId?: string;

  @ApiPropertyOptional({ description: 'Etiqueta de versión (auto si se omite: v1, v2, …)' })
  @IsOptional() @IsString()
  versionTag?: string;

  @ApiPropertyOptional({ type: HyperparamsDto })
  @IsOptional() @ValidateNested() @Type(() => HyperparamsDto)
  hyperparams?: HyperparamsDto;
}
