import { Column, CreateDateColumn, Entity, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';
import { numericTransformer } from '../../common/numeric.transformer';

export type LabelSource = 'human' | 'model';

@Entity({ schema: 'tfm_schema', name: 'segment_labels' })
export class SegmentLabelEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'segment_id', type: 'uuid' })
  segmentId!: string;

  @Column({ name: 'label_key', type: 'varchar', length: 60 })
  labelKey!: string;

  @Column({ type: 'varchar', length: 10 })
  source!: LabelSource;

  @Column({ type: 'numeric', precision: 5, scale: 4, nullable: true, transformer: numericTransformer })
  confidence?: number | null;

  @Column({ name: 'is_gold', type: 'boolean', default: false })
  isGold!: boolean;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt!: Date;

  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' })
  updatedAt!: Date;

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
