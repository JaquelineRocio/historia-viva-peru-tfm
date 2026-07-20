import { Column, Entity, PrimaryGeneratedColumn } from 'typeorm';

@Entity({ schema: 'tfm_schema', name: 'dataset_items' })
export class DatasetItemEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'dataset_id', type: 'uuid' })
  datasetId!: string;

  @Column({ name: 'segment_id', type: 'uuid', nullable: true })
  segmentId?: string | null;

  @Column({ name: 'resource_segment_id', type: 'uuid', nullable: true })
  resourceSegmentId?: string | null;

  @Column({ name: 'label_key', type: 'varchar', length: 60 })
  labelKey!: string;

  @Column({ type: 'text' })
  text!: string;

  @Column({ type: 'varchar', length: 10 })
  split!: 'train' | 'val' | 'test';
}
