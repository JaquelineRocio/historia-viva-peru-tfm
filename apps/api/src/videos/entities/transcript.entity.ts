import { Column, CreateDateColumn, Entity, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';

export type TranscriptSource = 'api' | 'whisper';

@Entity({ schema: 'tfm_schema', name: 'transcripts' })
export class TranscriptEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'video_id', type: 'uuid' })
  videoId!: string;

  @Column({ type: 'varchar', length: 10, nullable: true })
  language?: string | null;

  @Column({ type: 'varchar', length: 10 })
  source!: TranscriptSource;

  @Column({ name: 'is_generated', type: 'boolean', default: true })
  isGenerated!: boolean;

  @Column({ name: 'full_text', type: 'text', nullable: true })
  fullText?: string | null;

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
