import { HttpModule } from '@nestjs/axios';
import { Module } from '@nestjs/common';
import { HttpMlAdapter } from './http-ml.adapter';
import { ML_SERVICE_PORT } from './ml-service.port';

/**
 * Módulo del adaptador secundario ML. Expone el token `ML_SERVICE_PORT` para
 * que el dominio inyecte la interfaz, no la implementación HTTP concreta.
 */
@Module({
  imports: [HttpModule],
  providers: [{ provide: ML_SERVICE_PORT, useClass: HttpMlAdapter }],
  exports: [ML_SERVICE_PORT],
})
export class MlModule {}
