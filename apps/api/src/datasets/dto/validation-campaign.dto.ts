import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsInt, IsNotEmpty, IsNumber, IsOptional, IsString, Max, Min } from 'class-validator';

export class CreateValidationCampaignDto {
  @ApiPropertyOptional({ example: 'Segunda revisión — Dataset v1' })
  @IsOptional()
  @IsString()
  @IsNotEmpty()
  name?: string;

  @ApiPropertyOptional({ default: 0.2 })
  @IsOptional()
  @IsNumber()
  @Min(0.1)
  @Max(1)
  sampleRate?: number;

  @ApiPropertyOptional({ default: 42 })
  @IsOptional()
  @IsInt()
  seed?: number;
}

export class SecondaryAnnotationDto {
  @ApiProperty()
  @IsString()
  @IsNotEmpty()
  labelKey!: string;
}
