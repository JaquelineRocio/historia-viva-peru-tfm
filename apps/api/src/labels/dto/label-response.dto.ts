import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class TaxonomyResponseDto {
  @ApiProperty() key!: string;
  @ApiProperty() name!: string;
  @ApiPropertyOptional() description?: string | null;
  @ApiPropertyOptional() color?: string | null;
  @ApiProperty() sortOrder!: number;
}
