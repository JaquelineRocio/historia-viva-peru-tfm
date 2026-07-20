import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { TranscriptionStatus } from '../entities/video.entity';

export class VideoResponseDto {
  @ApiProperty() id!: string;
  @ApiProperty() youtubeId!: string;
  @ApiProperty() url!: string;
  @ApiPropertyOptional() title?: string | null;
  @ApiPropertyOptional() channel?: string | null;
  @ApiPropertyOptional() durationSec?: number | null;
  @ApiProperty({ enum: ['pending', 'processing', 'done', 'failed'] })
  transcriptionStatus!: TranscriptionStatus;
  @ApiProperty() createdAt!: Date;
}

export class SegmentResponseDto {
  @ApiProperty() id!: string;
  @ApiProperty() idx!: number;
  @ApiProperty() startSec!: number;
  @ApiProperty() endSec!: number;
  @ApiProperty() text!: string;
}

export class TranscriptResponseDto {
  @ApiProperty() id!: string;
  @ApiProperty() videoId!: string;
  @ApiPropertyOptional() language?: string | null;
  @ApiProperty({ enum: ['api', 'whisper'] }) source!: string;
  @ApiProperty() isGenerated!: boolean;
  @ApiProperty({ type: [SegmentResponseDto] }) segments!: SegmentResponseDto[];
}
