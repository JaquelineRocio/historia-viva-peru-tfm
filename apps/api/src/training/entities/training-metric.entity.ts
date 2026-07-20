import { Column, CreateDateColumn, Entity, PrimaryGeneratedColumn } from 'typeorm';
import { numericTransformer } from '../../common/numeric.transformer';

@Entity({ schema: 'tfm_schema', name: 'training_metrics' })
export class TrainingMetricEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'model_version_id', type: 'uuid' })
  modelVersionId!: string;

  @Column({ type: 'int', nullable: true })
  epoch?: number | null;

  @Column({ type: 'varchar', length: 10 })
  split!: string; // val | test

  @Column({ type: 'numeric', precision: 6, scale: 5, nullable: true, transformer: numericTransformer })
  accuracy?: number | null;

  @Column({ name: 'precision_macro', type: 'numeric', precision: 6, scale: 5, nullable: true, transformer: numericTransformer })
  precisionMacro?: number | null;

  @Column({ name: 'recall_macro', type: 'numeric', precision: 6, scale: 5, nullable: true, transformer: numericTransformer })
  recallMacro?: number | null;

  @Column({ name: 'f1_macro', type: 'numeric', precision: 6, scale: 5, nullable: true, transformer: numericTransformer })
  f1Macro?: number | null;

  @Column({ name: 'f1_weighted', type: 'numeric', precision: 6, scale: 5, nullable: true, transformer: numericTransformer })
  f1Weighted?: number | null;

  @Column({ name: 'f1_macro_ci95', type: 'jsonb', nullable: true })
  f1MacroCi95?: unknown;

  @Column({ name: 'results_by_source_type', type: 'jsonb', nullable: true })
  resultsBySourceType?: unknown;

  @Column({ name: 'baseline_name', type: 'varchar', length: 80, nullable: true })
  baselineName?: string | null;

  @Column({ name: 'baseline_f1_macro', type: 'numeric', precision: 6, scale: 5, nullable: true, transformer: numericTransformer })
  baselineF1Macro?: number | null;

  @Column({ name: 'baseline_dataset_sha256', type: 'varchar', length: 64, nullable: true })
  baselineDatasetSha256?: string | null;

  @Column({ name: 'exceeds_baseline', type: 'boolean', nullable: true })
  exceedsBaseline?: boolean | null;

  @Column({ name: 'per_class_metrics', type: 'jsonb', nullable: true })
  perClassMetrics?: unknown;

  @Column({ name: 'confusion_matrix', type: 'jsonb', nullable: true })
  confusionMatrix?: unknown;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt!: Date;
}
