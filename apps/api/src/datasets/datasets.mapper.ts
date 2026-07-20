import { DatasetEntity } from './entities/dataset.entity';
import { DatasetResponseDto } from './dto/dataset-response.dto';

/** Nunca exponemos entidades TypeORM: mapeamos a DTO. */
export const DatasetsMapper = {
  toDataset(e: DatasetEntity): DatasetResponseDto {
    return {
      id: e.id,
      name: e.name,
      description: e.description,
      nSamples: e.nSamples,
      classDistribution: e.classDistribution,
      splitConfig: e.splitConfig,
      createdAt: e.createdAt,
    };
  },
};
