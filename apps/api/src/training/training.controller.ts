import { Body, Controller, Get, Param, ParseUUIDPipe, Post, Query, UseGuards } from '@nestjs/common';
import { ApiBearerAuth, ApiOperation, ApiTags } from '@nestjs/swagger';
import { CurrentUser } from '../auth/current-user.decorator';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { AuthUser } from '../auth/jwt.strategy';
import { CreateTrainingJobDto, ImportModelDto } from './dto/training.dto';
import { InferenceService } from './inference.service';
import { TrainingMapper } from './training.mapper';
import { TrainingService } from './training.service';

@ApiTags('training')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller()
export class TrainingController {
  constructor(
    private readonly training: TrainingService,
    private readonly inference: InferenceService,
  ) {}

  // ---- jobs ----
  @Post('training/jobs')
  @ApiOperation({ summary: 'Lanzar entrenamiento (async) de una versión' })
  async createJob(@Body() dto: CreateTrainingJobDto, @CurrentUser() user: AuthUser) {
    return TrainingMapper.toJob(await this.training.createJob(dto, user.id));
  }

  @Get('training/jobs')
  @ApiOperation({ summary: 'Listar jobs de entrenamiento' })
  async listJobs() {
    const rows = await this.training.listJobs();
    return rows.map((j) => TrainingMapper.toJob(j));
  }

  @Get('training/jobs/:id')
  @ApiOperation({ summary: 'Estado de un job (polling)' })
  async getJob(@Param('id', ParseUUIDPipe) id: string) {
    return TrainingMapper.toJob(await this.training.getJob(id));
  }

  // ---- versions / models ----
  @Get('models')
  @ApiOperation({ summary: 'Listar versiones de modelo' })
  async listVersions() {
    const rows = await this.training.listVersions();
    return rows.map((v) => TrainingMapper.toVersion(v));
  }

  @Get('models/active')
  @ApiOperation({ summary: 'Versión activa' })
  async getActive() {
    const active = await this.training.getActive();
    return active ? TrainingMapper.toVersion(active) : null;
  }

  @Post('models/import')
  @ApiOperation({ summary: 'Registrar una versión entrenada fuera (Colab/Kaggle) con sus métricas' })
  async importModel(@Body() dto: ImportModelDto, @CurrentUser() user: AuthUser) {
    return TrainingMapper.toVersion(await this.training.importVersion(dto, user.id));
  }

  @Post('models/:id/activate')
  @ApiOperation({ summary: 'Activar una versión (la carga en el servicio ML)' })
  async activate(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return TrainingMapper.toVersion(await this.training.activate(id, user.role === 'admin'));
  }

  // ---- metrics ----
  @Get('metrics/models/:id')
  @ApiOperation({ summary: 'Métricas de una versión' })
  async metrics(@Param('id', ParseUUIDPipe) id: string) {
    const rows = await this.training.getMetrics(id);
    return rows.map((m) => TrainingMapper.toMetric(m));
  }

  @Get('metrics/compare')
  @ApiOperation({ summary: 'Comparar versiones (?ids=uuid,uuid)' })
  async compare(@Query('ids') ids: string) {
    const list = (ids ?? '').split(',').map((s) => s.trim()).filter(Boolean);
    const rows = await this.training.compare(list);
    return rows.map((r) => ({
      version: TrainingMapper.toVersion(r.version),
      metrics: r.metrics ? TrainingMapper.toMetric(r.metrics) : null,
    }));
  }

  // ---- inference ----
  @Post('inference/video/:id')
  @ApiOperation({ summary: 'Clasificar segmentos de un video con el modelo activo' })
  classifyVideo(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.inference.classifyVideo(id, user.id);
  }
}
