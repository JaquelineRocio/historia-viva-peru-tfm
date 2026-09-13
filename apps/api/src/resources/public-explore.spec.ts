import { BadRequestException, ConflictException, ForbiddenException, ServiceUnavailableException } from '@nestjs/common';
import { ResourcesService } from './resources.service';

const SESSION = '7f2554b0-e70a-4cad-b6b0-3f5c2e889807';

function serviceWith(options: {
  metadata?: { video_id: string; title: string; author: string; duration_sec: number; is_live: boolean };
  transaction?: (callback: (manager: unknown) => unknown) => unknown;
  duplicate?: { id: string; publicationStatus: string; processingStatus: string };
} = {}) {
  const configValues: Record<string, string> = {
    PUBLIC_PROCESSING_ENABLED: 'true',
    PUBLIC_PROCESS_MAX_DURATION_SEC: '7200',
    PUBLIC_PROCESS_RATE_WINDOW_HOURS: '24',
    PUBLIC_PROCESS_MAX_PER_SESSION: '1',
    PUBLIC_PROCESS_MAX_PER_IP: '5',
    JWT_SECRET: 'test-secret',
  };
  const config = { get: jest.fn((key: string, fallback?: string) => configValues[key] ?? fallback) };
  const ml = {
    inspectYoutube: jest.fn().mockResolvedValue(options.metadata ?? {
      video_id: 'gZpo1PjY0ao', title: 'Video real', author: 'Canal', duration_sec: 600, is_live: false,
    }),
  };
  const dataSource = {
    query: jest.fn().mockResolvedValue(options.duplicate ? [options.duplicate] : []),
    transaction: jest.fn(options.transaction ?? ((callback) => callback({
      query: jest.fn().mockResolvedValueOnce([]).mockResolvedValueOnce([{ sessionCount: 0, clientCount: 0 }]).mockResolvedValueOnce([]),
    }))),
  };
  return {
    service: new ResourcesService({} as never, {} as never, {} as never, ml as never, dataSource as never, config as never, {} as never),
    ml,
  };
}

describe('Public explore processing safeguards', () => {
  it.each([{ recentCount: 1, pendingCount: 0 }, { recentCount: 0, pendingCount: 2 }])('rejects overload before ML: %j', async (counts) => {
    const query = jest.fn().mockResolvedValueOnce([]).mockResolvedValueOnce([{ sessionCount: 0, clientCount: 0, ...counts }]);
    const { service, ml } = serviceWith({ transaction: (callback) => callback({ query }) });
    await expect(service.createPublicYoutube({ url: 'https://youtu.be/gZpo1PjY0ao', rightsConfirmed: true }, SESSION, '127.0.0.1')).rejects.toBeInstanceOf(ServiceUnavailableException);
    expect(ml.inspectYoutube).not.toHaveBeenCalled();
    expect(query.mock.calls[0][1]).toEqual(['public-processing-admission']);
    expect(query).toHaveBeenCalledTimes(2);
  });

  it('returns a controlled error when metadata inspection fails', async () => {
    const { service, ml } = serviceWith();
    ml.inspectYoutube.mockRejectedValue(new Error('upstream failure'));
    await expect(service.createPublicYoutube({ url: 'https://youtu.be/gZpo1PjY0ao', rightsConfirmed: true }, SESSION, '127.0.0.1')).rejects.toBeInstanceOf(ServiceUnavailableException);
  });
  it('rejects non-YouTube URLs before contacting the ML service', async () => {
    const { service, ml } = serviceWith();
    await expect(service.createPublicYoutube(
      { url: 'https://example.com/watch?v=gZpo1PjY0ao', rightsConfirmed: true }, SESSION, '127.0.0.1',
    )).rejects.toBeInstanceOf(BadRequestException);
    expect(ml.inspectYoutube).not.toHaveBeenCalled();
  });

  it('rejects videos over two hours using verified metadata', async () => {
    const { service } = serviceWith({
      metadata: { video_id: 'gZpo1PjY0ao', title: 'Largo', author: 'Canal', duration_sec: 7201, is_live: false },
    });
    await expect(service.createPublicYoutube(
      { url: 'https://www.youtube.com/watch?v=gZpo1PjY0ao', rightsConfirmed: true }, SESSION, '127.0.0.1',
    )).rejects.toThrow('supera el límite');
  });

  it('prevents a duplicate without exposing a private resource id', async () => {
    const { service } = serviceWith({ duplicate: { id: 'private-id', publicationStatus: 'private', processingStatus: 'ready' } });
    try {
      await service.createPublicYoutube(
        { url: 'https://youtu.be/gZpo1PjY0ao', rightsConfirmed: true }, SESSION, '127.0.0.1',
      );
      throw new Error('Expected duplicate rejection');
    } catch (error) {
      expect(error).toBeInstanceOf(ConflictException);
      expect((error as ConflictException).message).not.toContain('private-id');
    }
  });

  it('enforces both session and client quotas', async () => {
    const query = jest.fn()
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([{ sessionCount: 1, clientCount: 1 }]);
    const { service } = serviceWith({ transaction: (callback) => callback({ query }) });
    await expect(service.createPublicYoutube(
      { url: 'https://www.youtube.com/watch?v=gZpo1PjY0ao', rightsConfirmed: true }, SESSION, '127.0.0.1',
    )).rejects.toBeInstanceOf(ForbiddenException);
  });
});
