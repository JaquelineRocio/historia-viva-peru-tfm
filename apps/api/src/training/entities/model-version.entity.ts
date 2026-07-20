import { Column, CreateDateColumn, Entity, PrimaryGeneratedColumn } from 'typeorm';

export type ModelStatus = 'training' | 'ready' | 'failed';
export type ModelRecommendationStatus = 'experimental' | 'recommended';

@Entity({ schema: 'tfm_schema', name: 'model_versions' })
export class ModelVersionEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'version_tag', type: 'varchar', length: 30 })
  versionTag!: string;

  @Column({ name: 'dataset_id', type: 'uuid', nullable: true })
  datasetId?: string | null;

  @Column({ name: 'project_id', type: 'uuid', nullable: true })
  projectId?: string | null;

  @Column({ name: 'taxonomy_version_id', type: 'uuid', nullable: true })
  taxonomyVersionId?: string | null;

  @Column({ name: 'base_model', type: 'varchar', length: 200 })
  baseModel!: string;

  @Column({ name: 'parent_version_id', type: 'uuid', nullable: true })
  parentVersionId?: string | null;

  @Column({ type: 'jsonb', nullable: true })
  hyperparams?: Record<string, unknown> | null;

  @Column({ name: 'artifact_path', type: 'varchar', length: 400, nullable: true })
  artifactPath?: string | null;

  @Column({ type: 'varchar', length: 20, default: 'training' })
  status!: ModelStatus;

  @Column({ name: 'is_active', type: 'boolean', default: false })
  isActive!: boolean;

  @Column({ name: 'recommendation_status', type: 'varchar', length: 20, default: 'experimental' })
  recommendationStatus!: ModelRecommendationStatus;

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
