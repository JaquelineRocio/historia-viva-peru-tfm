import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsInt, IsNotEmpty, IsOptional, IsString, Max, Min } from 'class-validator';

export class CreateAnnotationCampaignDto {
  @ApiPropertyOptional({ example: 'Corpus gold v1' })
  @IsOptional()
  @IsString()
  @IsNotEmpty()
  name?: string;

  @ApiPropertyOptional({ default: 700 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(2000)
  targetCount?: number;

  @ApiPropertyOptional({ default: 42 })
  @IsOptional()
  @IsInt()
  seed?: number;

  @ApiPropertyOptional({ default: 150 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(500)
  maxPerSource?: number;
}
