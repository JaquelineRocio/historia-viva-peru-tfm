import { INestApplication } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import * as request from 'supertest';
import { AppController } from './app.controller';
import { ML_SERVICE_PORT } from './ml/ml-service.port';

describe('API health endpoints', () => {
  let app: INestApplication;
  const ml = { health: jest.fn() };

  beforeEach(async () => {
    ml.health.mockReset();
    const module = await Test.createTestingModule({
      controllers: [AppController],
      providers: [{ provide: ML_SERVICE_PORT, useValue: ml }],
    }).compile();
    app = module.createNestApplication();
    app.setGlobalPrefix('api');
    await app.init();
  });

  afterEach(async () => { await app.close(); });

  it('responds to Render without waiting for an unresponsive ML service', async () => {
    ml.health.mockImplementation(() => new Promise(() => {}));
    await request(app.getHttpServer()).get('/api/health/live')
      .timeout({ response: 1000, deadline: 2000 })
      .expect(200, { status: 'ok', service: 'api' });
    expect(ml.health).not.toHaveBeenCalled();
  });

  it('keeps external failure visible in the diagnostic endpoint', async () => {
    ml.health.mockRejectedValue(new Error('ML unavailable'));
    await request(app.getHttpServer()).get('/api/health')
      .expect(200, { status: 'ok', service: 'api', ml: 'unreachable' });
  });

  it('reports healthy ML through the diagnostic endpoint', async () => {
    ml.health.mockResolvedValue({ status: 'ok' });
    await request(app.getHttpServer()).get('/api/health')
      .expect(200, { status: 'ok', service: 'api', ml: 'ok' });
  });
});
