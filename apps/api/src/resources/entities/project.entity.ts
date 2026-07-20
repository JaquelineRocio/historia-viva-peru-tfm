import { Column, CreateDateColumn, Entity, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';

@Entity({ schema: 'tfm_schema', name: 'projects' })
export class ProjectEntity {
  @PrimaryGeneratedColumn('uuid') id!: string;
  @Column({ type: 'varchar', length: 200 }) name!: string;
  @Column({ type: 'text', nullable: true }) description?: string | null;
  @Column({ name: 'period_start', type: 'int', nullable: true }) periodStart?: number | null;
  @Column({ name: 'period_end', type: 'int', nullable: true }) periodEnd?: number | null;
  @Column({ name: 'is_public', type: 'boolean', default: false }) isPublic!: boolean;
  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' }) createdAt!: Date;
  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' }) updatedAt!: Date;
  @Column({ name: 'is_deleted', type: 'boolean', default: false }) isDeleted!: boolean;
  @Column({ name: 'created_user_id', type: 'uuid', nullable: true }) createdUserId?: string | null;
  @Column({ name: 'updated_user_id', type: 'uuid', nullable: true }) updatedUserId?: string | null;
}
