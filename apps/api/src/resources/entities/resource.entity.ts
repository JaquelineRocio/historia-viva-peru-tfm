import { Column, CreateDateColumn, Entity, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';

export type ResourceType = 'youtube' | 'pdf';
export type ProcessingStatus = 'pending' | 'processing' | 'ready' | 'needs_attention' | 'failed';

@Entity({ schema: 'tfm_schema', name: 'resources' })
export class ResourceEntity {
  @PrimaryGeneratedColumn('uuid') id!: string;
  @Column({ name: 'project_id', type: 'uuid' }) projectId!: string;
  @Column({ type: 'varchar', length: 20 }) type!: ResourceType;
  @Column({ type: 'varchar', length: 300 }) title!: string;
  @Column({ type: 'varchar', length: 200, nullable: true }) author?: string | null;
  @Column({ name: 'source_url', type: 'varchar', length: 1000, nullable: true }) sourceUrl?: string | null;
  @Column({ name: 'storage_path', type: 'varchar', length: 1000, nullable: true }) storagePath?: string | null;
  @Column({ name: 'storage_provider', type: 'varchar', length: 20, nullable: true }) storageProvider?: 'local' | 'r2' | null;
  @Column({ name: 'storage_key', type: 'varchar', length: 1000, nullable: true }) storageKey?: string | null;
  @Column({ name: 'original_filename', type: 'varchar', length: 300, nullable: true }) originalFilename?: string | null;
  @Column({ name: 'mime_type', type: 'varchar', length: 120, nullable: true }) mimeType?: string | null;
  @Column({ name: 'size_bytes', type: 'bigint', nullable: true }) sizeBytes?: string | null;
  @Column({ type: 'varchar', length: 64, nullable: true }) checksum?: string | null;
  @Column({ type: 'varchar', length: 80, nullable: true }) license?: string | null;
  @Column({ name: 'rights_confirmed', type: 'boolean', default: false }) rightsConfirmed!: boolean;
  @Column({ name: 'processing_status', type: 'varchar', length: 30, default: 'pending' }) processingStatus!: ProcessingStatus;
  @Column({ name: 'processing_error', type: 'text', nullable: true }) processingError?: string | null;
  @Column({ type: 'varchar', length: 10, nullable: true }) language?: string | null;
  @Column({ name: 'publication_status', type: 'varchar', length: 20, default: 'private' }) publicationStatus!: string;
  @Column({ name: 'file_publication_status', type: 'varchar', length: 20, default: 'private' }) filePublicationStatus!: string;
  @Column({ name: 'corpus_status', type: 'varchar', length: 20, default: 'candidate' }) corpusStatus!: 'candidate' | 'included' | 'excluded';
  @Column({ name: 'source_style', type: 'varchar', length: 30, nullable: true }) sourceStyle?: string | null;
  @Column({ name: 'corpus_notes', type: 'text', nullable: true }) corpusNotes?: string | null;
  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' }) createdAt!: Date;
  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' }) updatedAt!: Date;
  @Column({ name: 'is_deleted', type: 'boolean', default: false }) isDeleted!: boolean;
  @Column({ name: 'created_user_id', type: 'uuid', nullable: true }) createdUserId?: string | null;
  @Column({ name: 'updated_user_id', type: 'uuid', nullable: true }) updatedUserId?: string | null;
}
