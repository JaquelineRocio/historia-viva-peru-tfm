import { LabelsTaxonomyEntity } from './entities/labels-taxonomy.entity';
import { TaxonomyResponseDto } from './dto/label-response.dto';

/** Nunca exponemos entidades TypeORM: mapeamos a DTO. */
export const LabelsMapper = {
  toTaxonomy(e: LabelsTaxonomyEntity): TaxonomyResponseDto {
    return {
      key: e.key,
      name: e.name,
      description: e.description,
      color: e.color,
      sortOrder: e.sortOrder,
    };
  },
};
