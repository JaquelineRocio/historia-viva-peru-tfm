import { Column, CreateDateColumn, Entity, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';
import { numericTransformer } from '../../common/numeric.transformer';

@Entity({ schema: 'tfm_schema', name: 'segments' })
export class SegmentEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'video_id', type: 'uuid' })
  videoId!: string;

  @Column({ name: 'transcript_id', type: 'uuid' })
  transcriptId!: string;

  @Column({ type: 'int' })
  idx!: number;

  @Column({ name: 'start_sec', type: 'numeric', precision: 10, scale: 3, transformer: numericTransformer })
  startSec!: number;

  @Column({ name: 'end_sec', type: 'numeric', precision: 10, scale: 3, transformer: numericTransformer })
  endSec!: number;

  @Column({ type: 'text' })
  text!: string;

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
