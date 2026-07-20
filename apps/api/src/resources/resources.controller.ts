import { Body, Controller, Get, HttpCode, Param, ParseUUIDPipe, Patch, Post, Put, Query, Res, StreamableFile, UploadedFile, UseGuards, UseInterceptors } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import type { Response } from 'express';
import { CurrentUser } from '../auth/current-user.decorator';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { AuthUser } from '../auth/jwt.strategy';
import { AddCollectionItemDto, AssistantQueryDto, BulkReviewSegmentsDto, CorpusResourceDto, CreateCollectionDto, CreateProjectDto, CreateYoutubeResourceDto, EvidenceFeedbackDto, PdfMetadataDto, PublicationDecisionDto, ReplaceEntitiesDto, ReviewSegmentDto, SearchQueryDto, SegmentsQueryDto, UpdateResourceMetadataDto } from './dto/resource.dto';
import { ResourcesService } from './resources.service';

@UseGuards(JwtAuthGuard)
@Controller()
export class ResourcesController {
  constructor(private readonly service: ResourcesService) {}

  @Get('projects')
  listProjects(@CurrentUser() user: AuthUser) {
    return this.service.listProjects(user);
  }

  @Post('projects')
  createProject(@Body() dto: CreateProjectDto, @CurrentUser() user: AuthUser) {
    return this.service.createProject(dto, user.id);
  }

  @Get('projects/:id/dashboard')
  dashboard(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.service.dashboard(id, user);
  }

  @Get('projects/:id/resources')
  listResources(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.service.list(id, user);
  }

  @Post('projects/:id/resources/youtube')
  createYoutube(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: CreateYoutubeResourceDto,
    @CurrentUser() user: AuthUser,
  ) {
    return this.service.createYoutube(id, dto, user.id);
  }

  @Post('projects/:id/resources/pdf')
  @UseInterceptors(FileInterceptor('file', { limits: { fileSize: 50 * 1024 * 1024 } }))
  createPdf(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: PdfMetadataDto,
    @UploadedFile() file: { buffer: Buffer; size: number; mimetype: string; originalname: string },
    @CurrentUser() user: AuthUser,
  ) {
    return this.service.createPdf(id, dto, file, user.id);
  }

  @Get('resources/:id')
  findResource(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.service.findOne(id, user);
  }

  @Patch('resources/:id')
  updateResource(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: UpdateResourceMetadataDto,
    @CurrentUser() user: AuthUser,
  ) {
    return this.service.updateMetadata(id, dto, user);
  }

  @Get('resources/:id/file')
  async pdfFile(@Param('id', ParseUUIDPipe) id: string, @Res({ passthrough: true }) response: Response, @CurrentUser() user: AuthUser) {
    const file = await this.service.pdfFile(id, false, user);
    response.set({
      'Content-Type': 'application/pdf',
      'Content-Disposition': `inline; filename*=UTF-8''${encodeURIComponent(file.filename)}`,
      'Cache-Control': 'private, max-age=300',
    });
    return new StreamableFile(file.stream);
  }

  @Post('resources/:id/process')
  @HttpCode(202)
  process(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.service.process(id, user.id);
  }

  @Post('resources/:id/classify')
  classify(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.service.classifySegments(id, user);
  }

  @Get('resources/:id/segments')
  segments(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.service.listSegments(id, user);
  }

  @Get('projects/:projectId/resources/:resourceId/segments')
  pagedSegments(
    @Param('projectId', ParseUUIDPipe) projectId: string,
    @Param('resourceId', ParseUUIDPipe) resourceId: string,
    @Query() query: SegmentsQueryDto,
    @CurrentUser() user: AuthUser,
  ) {
    return this.service.listSegmentsPage(projectId, resourceId, query, user);
  }

  @Patch('resource-segments/:id/review')
  review(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: ReviewSegmentDto,
    @CurrentUser() user: AuthUser,
  ) {
    return this.service.review(id, dto, user.id);
  }

  @Post('segments/review/bulk')
  bulkReview(@Body() dto: BulkReviewSegmentsDto, @CurrentUser() user: AuthUser) {
    return this.service.bulkReview(dto.segmentIds, dto, user.id);
  }

  @Post('segments/:id/evidence-feedback')
  evidenceFeedback(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: EvidenceFeedbackDto,
    @CurrentUser() user: AuthUser,
  ) {
    return this.service.saveEvidenceFeedback(id, dto.value, dto.note, user.id);
  }

  @Get('resource-segments/:id/entities')
  segmentEntities(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.service.listSegmentEntities(id, user.id);
  }

  @Put('resource-segments/:id/entities')
  replaceSegmentEntities(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: ReplaceEntitiesDto,
    @CurrentUser() user: AuthUser,
  ) {
    return this.service.replaceSegmentEntities(id, dto.entities, user.id);
  }

  @Get('projects/:id/search')
  search(@Param('id', ParseUUIDPipe) id: string, @Query() query: SearchQueryDto, @CurrentUser() user: AuthUser) {
    return this.service.search(id, query.q || '', query, user);
  }

  @Get('projects/:id/search-facets')
  searchFacets(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.service.searchFacets(id, user);
  }

  @Post('projects/:id/assistant/query')
  assistant(@Param('id', ParseUUIDPipe) id: string, @Body() dto: AssistantQueryDto, @CurrentUser() user: AuthUser) {
    return this.service.assistant(id, dto.query, dto, user);
  }

  @Get('projects/:id/collections')
  collections(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.service.listCollections(id, user);
  }

  @Post('projects/:id/collections')
  createCollection(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: CreateCollectionDto,
    @CurrentUser() user: AuthUser,
  ) {
    return this.service.createCollection(id, dto.name, dto.description, user.id);
  }

  @Get('collections/:id')
  collection(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.service.collection(id, user);
  }

  @Post('collections/:id/items')
  addCollectionItem(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: AddCollectionItemDto,
    @CurrentUser() user: AuthUser,
  ) {
    return this.service.addCollectionItem(id, dto.segmentId, dto.note, user.id);
  }

  @Post('resources/:id/request-publication')
  requestPublication(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.service.requestPublication(id, user.id);
  }

  @Post('resources/:id/unpublish')
  unpublish(@Param('id', ParseUUIDPipe) id: string, @CurrentUser() user: AuthUser) {
    return this.service.unpublish(id, user);
  }

  @Patch('resources/:id/corpus')
  corpusStatus(@Param('id', ParseUUIDPipe) id: string, @Body() dto: CorpusResourceDto, @CurrentUser() user: AuthUser) {
    return this.service.setCorpusStatus(id, dto, user);
  }

  @Get('publication-reviews')
  publicationReviews(@CurrentUser() user: AuthUser) {
    return this.service.listPublicationReviews(user);
  }

  @Patch('publication-reviews/:id')
  decidePublication(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: PublicationDecisionDto,
    @CurrentUser() user: AuthUser,
  ) {
    return this.service.decidePublication(id, dto.status, dto.note, user);
  }
}

@Controller('public')
export class PublicResourcesController {
  constructor(private readonly service: ResourcesService) {}

  @Get('projects')
  projects() {
    return this.service.publicProjects();
  }

  @Get('projects/:id/resources')
  resources(@Param('id', ParseUUIDPipe) id: string) {
    return this.service.publicResources(id);
  }

  @Get('resources/:id/file')
  async pdfFile(@Param('id', ParseUUIDPipe) id: string, @Res({ passthrough: true }) response: Response) {
    const file = await this.service.pdfFile(id, true);
    response.set({
      'Content-Type': 'application/pdf',
      'Content-Disposition': `inline; filename*=UTF-8''${encodeURIComponent(file.filename)}`,
      'Cache-Control': 'public, max-age=3600',
    });
    return new StreamableFile(file.stream);
  }

  @Get('projects/:id/search')
  search(@Param('id', ParseUUIDPipe) id: string, @Query() query: SearchQueryDto) {
    return this.service.publicSearch(id, query.q || '', query);
  }
}
