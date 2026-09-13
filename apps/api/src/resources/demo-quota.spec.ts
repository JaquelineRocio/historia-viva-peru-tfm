import { ResourcesController } from './resources.controller';
import { ResourcesService } from './resources.service';

function setup(count = 3, mode = 'true', maximum = '3') {
  const projects = { findOne: jest.fn().mockResolvedValue({ id: 'project' }) };
  const resources = {
    count: jest.fn().mockResolvedValue(count),
    findOne: jest.fn().mockResolvedValue(null),
    create: jest.fn((value) => value),
    save: jest.fn(async (value) => value),
  };
  const dataSource = { query: jest.fn().mockResolvedValue([{}]) };
  const config = { get: jest.fn((key, fallback) => ({
    DEMO_MODE: mode, DEMO_MAX_SOURCES_PER_USER: maximum,
  }[key] ?? fallback)) };
  const storage = { put: jest.fn().mockResolvedValue({ provider: 'local', key: 'test.pdf' }) };
  const service = new ResourcesService(projects as never, resources as never, {} as never,
    {} as never, dataSource as never, config as never, storage as never);
  return { controller: new ResourcesController(service), resources, storage, dataSource };
}

describe.each(['youtube', 'pdf'])('Cuota de fuentes: %s', (type) => {
  function create(controller: ResourcesController, role: string, spoofRole = false) {
    const user = { id: 'owner', username: 'cuenta', role };
    const dto = { title: 'Fuente', url: 'https://www.youtube.com/watch?v=abcdefghijk',
      rightsConfirmed: true, ...(spoofRole ? { role: 'admin' } : {}) };
    if (type === 'youtube') return controller.createYoutube('project', dto, user);
    const buffer = Buffer.from('%PDF-1.4 sample');
    return controller.createPdf('project', dto,
      { buffer, size: buffer.length, mimetype: 'application/pdf', originalname: 'test.pdf' }, user);
  }

  it('permite al administrador crear fuentes aunque supere la cuota', async () => {
    const { controller, resources } = setup(20);
    await expect(create(controller, 'admin')).resolves.toMatchObject({ createdUserId: 'owner' });
    expect(resources.count).not.toHaveBeenCalled();
    expect(resources.save).toHaveBeenCalledTimes(1);
  });

  it.each(['colaborador', 'curador'])('mantiene el límite para %s', async (role) => {
    const { controller, resources, storage } = setup();
    await expect(create(controller, role)).rejects.toMatchObject({ status: 403 });
    expect(resources.count).toHaveBeenCalledWith({ where: { createdUserId: 'owner', isDeleted: false } });
    expect(resources.save).not.toHaveBeenCalled();
    expect(storage.put).not.toHaveBeenCalled();
  });

  it('permite la tercera fuente a una cuenta de demostración', async () => {
    const { controller } = setup(2);
    await expect(create(controller, 'colaborador')).resolves.toMatchObject({ createdUserId: 'owner' });
  });

  it('respeta una cuota configurada diferente', async () => {
    const { controller } = setup(5, 'true', '5');
    await expect(create(controller, 'colaborador')).rejects.toThrow('máximo de 5 fuentes');
  });

  it('no aplica la cuota cuando el modo demo está desactivado', async () => {
    const { controller, resources } = setup(20, 'false');
    await expect(create(controller, 'colaborador')).resolves.toBeDefined();
    expect(resources.count).not.toHaveBeenCalled();
  });

  it('un rol enviado en el cuerpo de la petición no concede la excepción', async () => {
    const { controller } = setup();
    await expect(create(controller, 'colaborador', true)).rejects.toMatchObject({ status: 403 });
  });

  it('conserva el control de acceso a proyectos para colaboradores', async () => {
    const { controller, dataSource, resources } = setup(0);
    dataSource.query.mockResolvedValue([]);
    await expect(create(controller, 'colaborador')).rejects.toThrow('No tienes acceso');
    expect(resources.save).not.toHaveBeenCalled();
  });
});
