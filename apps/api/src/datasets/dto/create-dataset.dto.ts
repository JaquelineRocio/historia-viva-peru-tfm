import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsInt, IsNotEmpty, IsNumber, IsOptional, IsString, Max, Min } from 'class-validator';

export class CreateDatasetDto {
  @ApiProperty({ example: 'Dataset v1 (independencia)' })
  @IsString()
  @IsNotEmpty()
  name!: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  description?: string;

  @ApiPropertyOptional({ default: 0.7, description: 'Proporción de train' })
  @IsOptional()
  @IsNumber()
  @Min(0.4)
  @Max(0.9)
  trainRatio?: number;

  @ApiPropertyOptional({ default: 0.15, description: 'Proporción de validación' })
  @IsOptional()
  @IsNumber()
  @Min(0.05)
  @Max(0.4)
  valRatio?: number;

  @ApiPropertyOptional({ default: 42 })
  @IsOptional()
  @IsInt()
  seed?: number;
}
