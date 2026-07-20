import { ApiProperty } from '@nestjs/swagger';
import { ArrayNotEmpty, IsArray, IsNotEmpty, IsString, IsUUID } from 'class-validator';

export class SetLabelDto {
  @ApiProperty({ example: 'campanias_militares' })
  @IsString()
  @IsNotEmpty()
  labelKey!: string;
}

export class BulkLabelDto {
  @ApiProperty({ type: [String], description: 'IDs de segmentos' })
  @IsArray()
  @ArrayNotEmpty()
  @IsUUID('4', { each: true })
  segmentIds!: string[];

  @ApiProperty({ example: 'personajes' })
  @IsString()
  @IsNotEmpty()
  labelKey!: string;
}
