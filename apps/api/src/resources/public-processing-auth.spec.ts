import { INestApplication } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { Test } from '@nestjs/testing';
import request = require('supertest');
import { AuthService } from '../auth/auth.service';
import { JwtStrategy } from '../auth/jwt.strategy';
import { PublicResourcesController } from './resources.controller';
import { ResourcesService } from './resources.service';

describe('Processing HTTP authentication', () => {
  let app: INestApplication;
  const userId = '7f2554b0-e70a-4cad-b6b0-3f5c2e889807';
  const secret = 'synthetic-auth-test-secret';
  const jwt = new JwtService({ secret });
  const service = {
    createPublicYoutube: jest.fn().mockResolvedValue({ stage: 'preparing_source' }),
    publicProcessingStatus: jest.fn().mockResolvedValue({ stage: 'ready' }),
    publicExplore: jest.fn().mockResolvedValue({ items: [] }),
  };
  const auth = { findActiveById: jest.fn() };

  beforeAll(async () => {
    const module = await Test.createTestingModule({
      imports: [PassportModule],
      controllers: [PublicResourcesController],
      providers: [JwtStrategy,
        { provide: ResourcesService, useValue: service },
        { provide: AuthService, useValue: auth },
        { provide: ConfigService, useValue: { get: () => secret } },
      ],
    }).compile();
    app = module.createNestApplication();
    await app.init();
  });
  beforeEach(() => {
    jest.clearAllMocks();
    auth.findActiveById.mockResolvedValue({ id: userId, username: 'test', role: 'collaborator' });
  });
  afterAll(async () => { await app.close(); });

  it.each(['missing', 'invalid', 'expired', 'inactive'])('rejects %s credentials before service execution', async (kind) => {
    const token = kind === 'invalid' ? 'invalid' : jwt.sign({ sub: userId }, { expiresIn: kind === 'expired' ? -1 : 60 });
    if (kind === 'inactive') auth.findActiveById.mockResolvedValue(null);
    const headers = kind === 'missing' ? {} : { Authorization: `Bearer ${token}` };
    await request(app.getHttpServer()).post('/public/explore/process').set(headers).send({}).expect(401);
    await request(app.getHttpServer()).get(`/public/explore/process/${userId}`).set(headers).expect(401);
    expect(service.createPublicYoutube).not.toHaveBeenCalled();
    expect(service.publicProcessingStatus).not.toHaveBeenCalled();
  });

  it('uses verified account identity instead of the caller session header', async () => {
    const headers = { Authorization: `Bearer ${jwt.sign({ sub: userId })}`, 'X-Demo-Session': 'forged-session' };
    const payload = { url: 'https://youtu.be/q_Frfn-MFUI', rightsConfirmed: true };
    await request(app.getHttpServer()).post('/public/explore/process').set(headers).send(payload).expect(202);
    expect(service.createPublicYoutube).toHaveBeenCalledWith(payload, userId, expect.any(String));
    await request(app.getHttpServer()).get(`/public/explore/process/${userId}`).set(headers).expect(200);
    expect(service.publicProcessingStatus).toHaveBeenCalledWith(userId, userId);
  });

  it('keeps the approved example catalog readable without credentials', async () => {
    await request(app.getHttpServer()).get('/public/explore/resources').expect(200);
  });
});
