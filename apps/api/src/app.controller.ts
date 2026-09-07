import { Controller, Get, Inject } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ML_SERVICE_PORT, MlServicePort } from './ml/ml-service.port';

@ApiTags('health')
@Controller()
export class AppController {
  constructor(@Inject(ML_SERVICE_PORT) private readonly ml: MlServicePort) {}

  @Get('health/live')
  @ApiOperation({ summary: 'Liveness de la API sin llamadas a servicios externos' })
  live() {
    // Render necesita una respuesta en menos de cinco segundos. Un arranque en
    // frío de Modal no debe provocar el reinicio de una API que sigue atendiendo.
    return { status: 'ok', service: 'api' };
  }

  @Get('health')
  @ApiOperation({ summary: 'Salud de la API y del servicio ML' })
  async health() {
    let mlStatus = 'down';
    try {
      mlStatus = (await this.ml.health()).status;
    } catch {
      mlStatus = 'unreachable';
    }
    return { status: 'ok', service: 'api', ml: mlStatus };
  }
}
