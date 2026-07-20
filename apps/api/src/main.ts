import { ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { AppModule } from './app.module';

async function bootstrap() {
  if (process.env.NODE_ENV === 'production' && (!process.env.JWT_SECRET || process.env.JWT_SECRET.startsWith('dev-'))) {
    throw new Error('JWT_SECRET debe configurarse con un secreto seguro en producción');
  }
  const app = await NestFactory.create(AppModule);
  app.getHttpAdapter().getInstance().set('trust proxy', 1);

  // Todas las rutas bajo /api (el proxy de Vite reenvía /api → :3000).
  app.setGlobalPrefix('api');

  app.useGlobalPipes(
    new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }),
  );

  // En producción solo se acepta el dominio del frontend. En desarrollo se
  // conserva el comportamiento abierto para localhost.
  const webOrigins = (process.env.WEB_ORIGIN || '')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean);
  app.enableCors({ origin: webOrigins.length ? webOrigins : true, credentials: true });

  const config = new DocumentBuilder()
    .setTitle('TFM API — Clasificador de subtemas (Independencia del Perú)')
    .setDescription('Orquestador NestJS: auth, videos, transcripción. Delega ML al servicio Python.')
    .setVersion('0.2.0')
    .addBearerAuth()
    .build();
  SwaggerModule.setup('api/docs', app, SwaggerModule.createDocument(app, config));

  const port = process.env.PORT ?? 3000;
  await app.listen(port);
  // eslint-disable-next-line no-console
  console.log(`API en http://localhost:${port}/api  ·  Swagger en /api/docs`);
}
bootstrap();
