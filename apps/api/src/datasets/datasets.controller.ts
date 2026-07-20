import { Body, Controller, Get, Param, ParseUUIDPipe, Patch, Post, Query, UseGuards } from '@nestjs/common';
import { ApiBearerAuth, ApiOperation, ApiTags } from '@nestjs/swagger';
import { CurrentUser } from '../auth/current-user.decorator';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { AuthUser } from '../auth/jwt.strategy';
import { CreateDatasetDto } from './dto/create-dataset.dto';
import { CreateValidationCampaignDto, SecondaryAnnotationDto } from './dto/validation-campaign.dto';
import { CreateAnnotationCampaignDto } from './dto/annotation-campaign.dto';
import { DatasetsMapper } from './datasets.mapper';
import { DatasetsService } from './datasets.service';

@ApiTags('datasets')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('datasets')
export class DatasetsController {
  constructor(private readonly datasets: DatasetsService) {}

  @Get('readiness')
  @ApiOperation({ summary: 'Preparación del corpus por clase antes de crear un snapshot' })
  readiness() {
    return this.datasets.readiness();
  }

  @Post()
  @ApiOperation({ summary: 'Crear snapshot inmutable del dataset (desde etiquetas gold)' })
  async create(@Body() dto: CreateDatasetDto, @CurrentUser() user: AuthUser) {
    return DatasetsMapper.toDataset(await this.datasets.createSnapshot(dto, user.id));
  }

  @Get()
  @ApiOperation({ summary: 'Listar datasets' })
  async findAll() {
    const rows = await this.datasets.findAll();
    return rows.map((d) => DatasetsMapper.toDataset(d));
  }

  @Get(':id')
  @ApiOperation({ summary: 'Detalle de un dataset (distribución de clases y split)' })
  async findOne(@Param('id', ParseUUIDPipe) id: string) {
    return DatasetsMapper.toDataset(await this.datasets.findOneOrFail(id));
  }

  @Get(':id/export')
  @ApiOperation({ summary: 'Exportar items (para Colab / respaldo): [{text,label,split}]' })
  async export(@Param('id', ParseUUIDPipe) id: string) {
    const dataset = await this.datasets.findOneOrFail(id);
    const items = await this.datasets.getExportItems(id);
    const labels = [...new Set(items.map((i) => i.labelKey))].sort();
    return {
      dataset: { id: dataset.id, name: dataset.name, splitConfig: dataset.splitConfig },
      labels,
      items: items.map((i) => ({
        text: i.text,
        label: i.labelKey,
        split: i.split,
        resourceId: i.resourceId,
        sourceType: i.sourceType,
      })),
    };
  }
}

@ApiTags('project datasets')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('projects/:projectId/datasets')
export class ProjectDatasetsController {
  constructor(private readonly datasets: DatasetsService) {}

  @Get('readiness')
  async readiness(@Param('projectId', ParseUUIDPipe) projectId: string, @CurrentUser() user: AuthUser) {
    await this.datasets.assertProjectAccess(projectId, user);
    return this.datasets.readiness(projectId);
  }

  @Post()
  async create(@Param('projectId', ParseUUIDPipe) projectId: string, @Body() dto: CreateDatasetDto, @CurrentUser() user: AuthUser) {
    await this.datasets.assertProjectAccess(projectId, user);
    return DatasetsMapper.toDataset(await this.datasets.createSnapshot(dto, user.id, projectId));
  }

  @Get()
  async findAll(@Param('projectId', ParseUUIDPipe) projectId: string, @CurrentUser() user: AuthUser) {
    await this.datasets.assertProjectAccess(projectId, user);
    return (await this.datasets.findAllByProject(projectId)).map((dataset) => DatasetsMapper.toDataset(dataset));
  }
}

@ApiTags('annotation validation')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller()
export class ValidationCampaignsController {
  constructor(private readonly datasets: DatasetsService) {}

  @Post('projects/:projectId/annotation-campaigns')
  createAnnotationCampaign(
    @Param('projectId', ParseUUIDPipe) projectId: string,
    @Body() dto: CreateAnnotationCampaignDto,
    @CurrentUser() user: AuthUser,
  ) {
    return this.datasets.createAnnotationCampaign(projectId, dto, user);
  }

  @Get('projects/:projectId/annotation-campaigns')
  annotationCampaigns(@Param('projectId', ParseUUIDPipe) projectId: string, @CurrentUser() user: AuthUser) {
    return this.datasets.listAnnotationCampaigns(projectId, user);
  }

  @Get('annotation-campaigns/:campaignId/progress')
  annotationCampaignProgress(
    @Param('campaignId', ParseUUIDPipe) campaignId: string,
    @CurrentUser() user: AuthUser,
  ) {
    return this.datasets.annotationCampaignProgress(campaignId, user);
  }

  @Post('projects/:projectId/validation-campaigns')
  createCampaign(
    @Param('projectId', ParseUUIDPipe) projectId: string,
    @Body() dto: CreateValidationCampaignDto,
    @CurrentUser() user: AuthUser,
  ) {
    return this.datasets.createValidationCampaign(projectId, dto, user);
  }

  @Get('projects/:projectId/validation-campaigns')
  campaigns(@Param('projectId', ParseUUIDPipe) projectId: string, @CurrentUser() user: AuthUser) {
    return this.datasets.listValidationCampaigns(projectId, user);
  }

  @Get('validation-campaigns/:campaignId/samples')
  samples(
    @Param('campaignId', ParseUUIDPipe) campaignId: string,
    @Query('page') page: string,
    @Query('limit') limit: string,
    @CurrentUser() user: AuthUser,
  ) {
    return this.datasets.validationSamples(campaignId, Number(page) || 1, Number(limit) || 25, user);
  }

  @Patch('validation-samples/:sampleId')
  annotate(
    @Param('sampleId', ParseUUIDPipe) sampleId: string,
    @Body() dto: SecondaryAnnotationDto,
    @CurrentUser() user: AuthUser,
  ) {
    return this.datasets.saveSecondaryAnnotation(sampleId, dto.labelKey, user);
  }

  @Get('validation-campaigns/:campaignId/agreement')
  agreement(@Param('campaignId', ParseUUIDPipe) campaignId: string, @CurrentUser() user: AuthUser) {
    return this.datasets.validationAgreement(campaignId, user);
  }
}
