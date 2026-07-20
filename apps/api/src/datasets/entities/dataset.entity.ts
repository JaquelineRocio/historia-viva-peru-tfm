import { Column, CreateDateColumn, Entity, PrimaryGeneratedColumn } from 'typeorm';

@Entity({ schema: 'tfm_schema', name: 'datasets' })
export class DatasetEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'project_id', type: 'uuid', nullable: true })
  projectId?: string | null;

  @Column({ type: 'varchar', length: 150 })
  name!: string;

  @Column({ type: 'text', nullable: true })
  description?: string | null;

  @Column({ name: 'n_samples', type: 'int', default: 0 })
  nSamples!: number;

  @Column({ name: 'class_distribution', type: 'jsonb', nullable: true })
  classDistribution?: Record<string, number> | null;

  @Column({ name: 'split_config', type: 'jsonb', nullable: true })
  splitConfig?: Record<string, unknown> | null;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt!: Date;

  @Column({ name: 'is_deleted', type: 'boolean', default: false })
  isDeleted!: boolean;

  @Column({ name: 'deleted_at', type: 'timestamptz', nullable: true })
  deletedAt?: Date | null;

  @Column({ name: 'created_user_id', type: 'uuid', nullable: true })
  createdUserId?: string | null;

  @Column({ name: 'updated_user_id', type: 'uuid', nullable: true })
  updatedUserId?: string | null;

  @Column({ name: 'deleted_user_id', type: 'uuid', nullable: true })
  deletedUserId?: string | null;
}
