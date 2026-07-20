import { Column, CreateDateColumn, Entity, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';

export type TranscriptionStatus = 'pending' | 'processing' | 'done' | 'failed';

@Entity({ schema: 'tfm_schema', name: 'videos' })
export class VideoEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'youtube_id', type: 'varchar', length: 20 })
  youtubeId!: string;

  @Column({ type: 'varchar', length: 500 })
  url!: string;

  @Column({ type: 'varchar', length: 300, nullable: true })
  title?: string | null;

  @Column({ type: 'varchar', length: 200, nullable: true })
  channel?: string | null;

  @Column({ name: 'duration_sec', type: 'int', nullable: true })
  durationSec?: number | null;

  @Column({ name: 'transcription_status', type: 'varchar', length: 20, default: 'pending' })
  transcriptionStatus!: TranscriptionStatus;

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
