import { Logger } from '@nestjs/common';
import { ResourcesService } from './resources.service';

function setup() {
  const projects = { findOne: jest.fn().mockResolvedValue({ id: 'project' }) };
  const resources = {
    findOne: jest.fn().mockResolvedValue({ id: 'pdf', projectId: 'project', storageProvider: 's3', storageKey: 'project/file.pdf' }),
    create: jest.fn((value) => value),
    save: jest.fn(),
  };
  const storage = { get: jest.fn(), put: jest.fn() };
  const dataSource = { query: jest.fn().mockResolvedValue([{}]) };
  const config = { get: jest.fn((_key, fallback) => fallback) };
  const service = new ResourcesService(projects as never, resources as never, {} as never,
    {} as never, dataSource as never, config as never, storage as never);
  return { service, resources, storage };
}

describe('PDF storage failures', () => {
  beforeEach(() => { jest.spyOn(Logger.prototype, 'warn').mockImplementation(() => {}); });
  afterEach(() => { jest.restoreAllMocks(); });

  it('reports a Storage database timeout as 503 instead of a missing document', async () => {
    const { service, storage } = setup();
    storage.get.mockRejectedValue(Object.assign(new Error('The connection to the database timed out'), { name: 'DatabaseTimeout' }));
    await expect(service.pdfFile('pdf')).rejects.toMatchObject({ status: 503 });
  });

  it.each([{ name: 'NoSuchKey' }, { code: 'ENOENT' }])('reports a missing S3 or local file as 404: %j', async (error) => {
    const { service, storage } = setup();
    storage.get.mockRejectedValue(error);
    await expect(service.pdfFile('pdf')).rejects.toMatchObject({ status: 404 });
  });

  it('does not describe an inaccessible bucket as a deleted PDF', async () => {
    const { service, storage } = setup();
    storage.get.mockRejectedValue({ name: 'NoSuchBucket' });
    await expect(service.pdfFile('pdf')).rejects.toMatchObject({ status: 503 });
  });

  it('returns PDF content when storage responds', async () => {
    const { service, storage } = setup();
    const content = Buffer.from('%PDF-1.4');
    storage.get.mockResolvedValue(content);
    await expect(service.pdfFile('pdf')).resolves.toMatchObject({ stream: content });
  });

  it('reports failed uploads as 503 without creating a resource record', async () => {
    const { service, storage, resources } = setup();
    resources.findOne.mockResolvedValue(null);
    storage.put.mockRejectedValue(Object.assign(new Error('The connection to the database timed out'), { name: 'DatabaseTimeout' }));
    const buffer = Buffer.from('%PDF-1.4 sample');
    await expect(service.createPdf('project', { title: 'Test', rightsConfirmed: true },
      { buffer, size: buffer.length, mimetype: 'application/pdf', originalname: 'test.pdf' }, 'user'))
      .rejects.toMatchObject({ status: 503 });
    expect(resources.save).not.toHaveBeenCalled();
  });
});
