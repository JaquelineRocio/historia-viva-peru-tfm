import { Column, CreateDateColumn, Entity, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';
import { numericTransformer } from '../../common/numeric.transformer';

export type ReviewStatus = 'pending' | 'reviewed' | 'ambiguous' | 'excluded';

@Entity({ schema: 'tfm_schema', name: 'resource_segments' })
export class ResourceSegmentEntity {
  @PrimaryGeneratedColumn('uuid') id!: string;
  @Column({ name: 'resource_id', type: 'uuid' }) resourceId!: string;
  @Column({ type: 'int' }) idx!: number;
  @Column({ name: 'locator_type', type: 'varchar', length: 20 }) locatorType!: 'timestamp' | 'page';
  @Column({ name: 'start_sec', type: 'numeric', precision: 10, scale: 3, nullable: true, transformer: numericTransformer }) startSec?: number | null;
  @Column({ name: 'end_sec', type: 'numeric', precision: 10, scale: 3, nullable: true, transformer: numericTransformer }) endSec?: number | null;
  @Column({ name: 'page_start', type: 'int', nullable: true }) pageStart?: number | null;
  @Column({ name: 'page_end', type: 'int', nullable: true }) pageEnd?: number | null;
  @Column({ type: 'text' }) text!: string;
  @Column({ name: 'suggested_label_key', type: 'varchar', length: 60, nullable: true }) suggestedLabelKey?: string | null;
  @Column({ name: 'suggested_confidence', type: 'numeric', precision: 6, scale: 5, nullable: true, transformer: numericTransformer }) suggestedConfidence?: number | null;
  @Column({ name: 'review_status', type: 'varchar', length: 20, default: 'pending' }) reviewStatus!: ReviewStatus;
  @Column({ name: 'reviewed_label_key', type: 'varchar', length: 60, nullable: true }) reviewedLabelKey?: string | null;
  @Column({ name: 'reviewed_user_id', type: 'uuid', nullable: true }) reviewedUserId?: string | null;
  @Column({ name: 'reviewed_at', type: 'timestamptz', nullable: true }) reviewedAt?: Date | null;
  @Column({ name: 'is_deleted', type: 'boolean', default: false }) isDeleted!: boolean;
  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' }) createdAt!: Date;
  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' }) updatedAt!: Date;
}
