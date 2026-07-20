import { Body, Controller, Get, Param, ParseUUIDPipe, Post, UseGuards } from '@nestjs/common';
import { ApiBearerAuth, ApiOperation, ApiTags } from '@nestjs/swagger';
import { CurrentUser } from '../auth/current-user.decorator';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { AuthUser } from '../auth/jwt.strategy';
import { BulkLabelDto, SetLabelDto } from './dto/label.dto';
import { LabelsMapper } from './labels.mapper';
import { LabelsService } from './labels.service';

@ApiTags('labels')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller()
export class LabelsController {
  constructor(private readonly labels: LabelsService) {}

  @Get('labels/taxonomy')
  @ApiOperation({ summary: 'Catálogo de subtemas (colores incluidos)' })
  async taxonomy() {
    const rows = await this.labels.getTaxonomy();
    return rows.map((t) => LabelsMapper.toTaxonomy(t));
  }

  @Get('labels/by-video/:videoId')
  @ApiOperation({ summary: 'Mapa segmentId → etiqueta activa (para LabelingPage)' })
  async byVideo(@Param('videoId', ParseUUIDPipe) videoId: string) {
    // Nota: se filtra por los segmentos del video en el cliente combinando con la transcripción.
    // Aquí devolvemos todas las etiquetas activas de los segmentos existentes del video.
    return this.labels.getLabelsForVideo(videoId);
  }

  @Post('segments/:id/label')
  @ApiOperation({ summary: 'Etiquetar (gold) un segmento' })
  async setLabel(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: SetLabelDto,
    @CurrentUser() user: AuthUser,
  ) {
    const saved = await this.labels.setHuman(id, dto.labelKey, user.id);
    return { segmentId: saved.segmentId, labelKey: saved.labelKey, source: saved.source, isGold: saved.isGold };
  }

  @Post('segments/bulk-label')
  @ApiOperation({ summary: 'Etiquetar (gold) varios segmentos con el mismo subtema' })
  async bulkLabel(@Body() dto: BulkLabelDto, @CurrentUser() user: AuthUser) {
    const n = await this.labels.bulkSetHuman(dto.segmentIds, dto.labelKey, user.id);
    return { labeled: n };
  }
}
