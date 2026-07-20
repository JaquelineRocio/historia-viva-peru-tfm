import { Column, CreateDateColumn, Entity, PrimaryGeneratedColumn } from 'typeorm';

export type JobStatus = 'queued' | 'running' | 'done' | 'failed' | 'cancelled';

@Entity({ schema: 'tfm_schema', name: 'training_jobs' })
export class TrainingJobEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'model_version_id', type: 'uuid', nullable: true })
  modelVersionId?: string | null;

  @Column({ name: 'dataset_id', type: 'uuid', nullable: true })
  datasetId?: string | null;

  @Column({ name: 'ml_job_id', type: 'varchar', length: 80, nullable: true })
  mlJobId?: string | null;

  @Column({ type: 'varchar', length: 20, default: 'queued' })
  status!: JobStatus;

  @Column({ type: 'int', default: 0 })
  progress!: number;

  @Column({ name: 'current_epoch', type: 'int', nullable: true })
  currentEpoch?: number | null;

  @Column({ type: 'text', nullable: true })
  logs?: string | null;

  @Column({ type: 'text', nullable: true })
  error?: string | null;

  @Column({ name: 'started_at', type: 'timestamptz', nullable: true })
  startedAt?: Date | null;

  @Column({ name: 'finished_at', type: 'timestamptz', nullable: true })
  finishedAt?: Date | null;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt!: Date;
}
