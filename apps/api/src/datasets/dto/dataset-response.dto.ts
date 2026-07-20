import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class DatasetResponseDto {
  @ApiProperty() id!: string;
  @ApiProperty() name!: string;
  @ApiPropertyOptional() description?: string | null;
  @ApiProperty() nSamples!: number;
  @ApiPropertyOptional() classDistribution?: Record<string, number> | null;
  @ApiPropertyOptional() splitConfig?: Record<string, unknown> | null;
  @ApiProperty() createdAt!: Date;
}
