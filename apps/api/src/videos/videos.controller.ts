import {
  Body,
  ConflictException,
  Controller,
  Delete,
  Get,
  HttpCode,
  NotFoundException,
  Param,
  ParseUUIDPipe,
  Post,
  UseGuards,
} from '@nestjs/common';
import { ApiBearerAuth, ApiOperation, ApiTags } from '@nestjs/swagger';
import { CurrentUser } from '../auth/current-user.decorator';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { AuthUser } from '../auth/jwt.strategy';
import { CreateVideoDto } from './dto/create-video.dto';
import { VideosMapper } from './videos.mapper';
import { VideosService } from './videos.service';
import { TranscriptionService } from './transcription.service';

@ApiTags('videos')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('videos')
export class VideosController {
  constructor(
    private readonly videosService: VideosService,
    private readonly transcriptionService: TranscriptionService,
  ) {}

  @Post()
  @ApiOperation({ summary: 'Ingerir un video de YouTube (pending)' })
  async create(@Body() dto: CreateVideoDto, @CurrentUser() user: AuthUser) {
    const video = await this.videosService.create(dto, user.id);
    return VideosMapper.toVideo(video);
  }

  @Get()
  @ApiOperation({ summary: 'Listar videos ingeridos' })
  async findAll() {
    const videos = await this.videosService.findAll();
    return videos.map((v) => VideosMapper.toVideo(v));
  }

  @Get(':id')
  @ApiOperation({ summary: 'Detalle de un video (incluye estado de transcripción)' })
  async findOne(@Param('id', ParseUUIDPipe) id: string) {
    const video = await this.videosService.findOneOrFail(id);
    return VideosMapper.toVideo(video);
  }

  @Post(':id/transcribe')
  @HttpCode(202)
  @ApiOperation({ summary: 'Lanzar transcripción (async): subtítulos → fallback Whisper → segmentar' })
  async transcribe(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    const video = await this.videosService.findOneOrFail(id);
    if (video.transcriptionStatus === 'processing')
      throw new ConflictException('Este video ya tiene una transcripción en curso');
    // El estado se marca ANTES de responder: así el polling del front ve
    // `processing` desde el primer refetch y no se lanzan cascadas duplicadas.
    await this.transcriptionService.markProcessing(video.id, user.id);
    // Fire-and-forget: corre en segundo plano; el front hace polling de GET :id.
    void this.transcriptionService.run(video.id, user.id);
    return { accepted: true, videoId: video.id, status: 'processing' };
  }

  @Get(':id/transcript')
  @ApiOperation({ summary: 'Transcripción + segmentos con timestamps' })
  async transcript(@Param('id', ParseUUIDPipe) id: string) {
    await this.videosService.findOneOrFail(id);
    const result = await this.videosService.getTranscript(id);
    if (!result) throw new NotFoundException('Este video aún no tiene transcripción');
    return VideosMapper.toTranscript(result.transcript, result.segments);
  }

  @Delete(':id')
  @HttpCode(204)
  @ApiOperation({ summary: 'Eliminar (soft delete) un video y su transcripción' })
  async remove(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    await this.videosService.softDelete(id, user.id);
  }
}
