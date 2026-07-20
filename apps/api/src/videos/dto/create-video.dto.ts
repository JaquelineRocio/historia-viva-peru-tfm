import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsNotEmpty, IsOptional, IsString, MaxLength } from 'class-validator';

export class CreateVideoDto {
  @ApiProperty({ example: 'https://www.youtube.com/watch?v=rKbC4guGhRY', description: 'URL o ID de YouTube' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(500)
  url!: string;

  @ApiPropertyOptional({ example: 'Independencia del Perú — resumen' })
  @IsOptional()
  @IsString()
  @MaxLength(300)
  title?: string;

  @ApiPropertyOptional({ example: 'Canal de Historia' })
  @IsOptional()
  @IsString()
  @MaxLength(200)
  channel?: string;
}
