import { Injectable, Logger, UnauthorizedException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import { InjectRepository } from '@nestjs/typeorm';
import * as bcrypt from 'bcryptjs';
import { Repository } from 'typeorm';
import { UserEntity } from './entities/user.entity';
import { LoginDto } from './dto/login.dto';

@Injectable()
export class AuthService {
  private readonly logger = new Logger(AuthService.name);

  constructor(
    @InjectRepository(UserEntity) private readonly users: Repository<UserEntity>,
    private readonly jwt: JwtService,
    private readonly config: ConfigService,
  ) {}

  /** Crea el usuario de prueba del TFM si aún no existe (idempotente). */
  async seedTestUser(): Promise<void> {
    const username = this.config.get<string>('SEED_USERNAME', 'docente');
    const password = this.config.get<string>('SEED_PASSWORD', 'tfm2026');
    const role = this.config.get<string>('SEED_ROLE', 'colaborador');
    try {
      const existing = await this.users.findOne({ where: { username, isDeleted: false } });
      if (existing) {
        if (existing.role !== role) await this.users.update(existing.id, { role });
        return;
      }
      const hashed = await bcrypt.hash(password, 10);
      await this.users.save(
        this.users.create({
          username,
          hashedPassword: hashed,
          displayName: this.config.get<string>('SEED_DISPLAY_NAME', 'Docente de prueba'),
          role,
        }),
      );
      this.logger.log(`Usuario de prueba creado: ${username}`);
    } catch (err) {
      // La BD puede no estar lista aún en dev; no bloquea el arranque.
      this.logger.warn(`No se pudo sembrar el usuario de prueba: ${(err as Error).message}`);
    }
  }

  /** Cuenta separada para que la segunda revisión del TFM sea independiente. */
  async seedSecondaryReviewer(): Promise<void> {
    if (this.config.get<string>('SEED_SECOND_REVIEWER', 'false') !== 'true') return;
    const username = this.config.get<string>('SECOND_REVIEWER_USERNAME', 'especialista');
    const password = this.config.get<string>('SECOND_REVIEWER_PASSWORD', 'tfm2026');
    try {
      const existing = await this.users.findOne({ where: { username, isDeleted: false } });
      if (existing) return;
      await this.users.save(this.users.create({
        username,
        hashedPassword: await bcrypt.hash(password, 10),
        displayName: this.config.get<string>('SECOND_REVIEWER_DISPLAY_NAME', 'Especialista revisor'),
        role: 'colaborador',
      }));
      this.logger.log(`Cuenta de segundo revisor creada: ${username}`);
    } catch (err) {
      this.logger.warn(`No se pudo sembrar el segundo revisor: ${(err as Error).message}`);
    }
  }

  /** Crea una cuenta administrativa solo cuando el deploy proporciona un secreto. */
  async seedAdmin(): Promise<void> {
    const password = this.config.get<string>('ADMIN_PASSWORD');
    if (!password) return;
    const username = this.config.get<string>('ADMIN_USERNAME', 'administrador');
    try {
      const existing = await this.users.findOne({ where: { username, isDeleted: false } });
      if (existing) {
        const changes: Partial<UserEntity> = {};
        if (existing.role !== 'admin') changes.role = 'admin';
        if (!(await bcrypt.compare(password, existing.hashedPassword))) changes.hashedPassword = await bcrypt.hash(password, 10);
        if (Object.keys(changes).length) await this.users.update(existing.id, changes);
        return;
      }
      await this.users.save(this.users.create({
        username,
        hashedPassword: await bcrypt.hash(password, 10),
        displayName: 'Administración TFM',
        role: 'admin',
      }));
      this.logger.log('Cuenta administrativa configurada mediante secreto');
    } catch (err) {
      this.logger.warn(`No se pudo configurar la cuenta administrativa: ${(err as Error).message}`);
    }
  }

  async findActiveById(id: string): Promise<UserEntity | null> {
    return this.users.findOne({ where: { id, isDeleted: false } });
  }

  async login(dto: LoginDto): Promise<{ accessToken: string; user: { id: string; username: string; role: string; displayName?: string | null } }> {
    const user = await this.users.findOne({ where: { username: dto.username, isDeleted: false } });
    if (!user) throw new UnauthorizedException('Credenciales inválidas');

    const ok = await bcrypt.compare(dto.password, user.hashedPassword);
    if (!ok) throw new UnauthorizedException('Credenciales inválidas');

    const accessToken = await this.jwt.signAsync({ sub: user.id, username: user.username, role: user.role });
    return {
      accessToken,
      user: { id: user.id, username: user.username, role: user.role, displayName: user.displayName },
    };
  }
}
