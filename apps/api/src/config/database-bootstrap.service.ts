import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { InjectDataSource } from '@nestjs/typeorm';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { DataSource } from 'typeorm';
import { AuthService } from '../auth/auth.service';

/**
 * Bootstrap del esquema: si `tfm_schema.users` no existe, ejecuta ddl.sql
 * (fuente de verdad). Hace el deploy indoloro (Postgres gestionado no corre
 * init-scripts) y también sirve en local sin docker-compose.
 */
@Injectable()
export class DatabaseBootstrapService implements OnModuleInit {
  private readonly logger = new Logger(DatabaseBootstrapService.name);

  constructor(
    @InjectDataSource() private readonly dataSource: DataSource,
    private readonly config: ConfigService,
    private readonly auth: AuthService,
  ) {}

  async onModuleInit(): Promise<void> {
    try {
      const exists = await this.dataSource.query(`SELECT to_regclass('tfm_schema.users') AS t`);
      if (!exists?.[0]?.t) {
        const ddlPath = this.resolveDdlPath();
        if (ddlPath) {
          await this.dataSource.query(readFileSync(ddlPath, 'utf-8'));
          this.logger.log(`Esquema creado desde ${ddlPath}`);
        } else {
          this.logger.warn('No se encontró ddl.sql; se omite el bootstrap del esquema.');
        }
      }
      const evolutionPath = this.resolveEvolutionPath();
      if (evolutionPath) {
        await this.dataSource.query(readFileSync(evolutionPath, 'utf-8'));
        this.logger.log('Evolución Historia Viva aplicada');
      }
      // El esquema ya existe: sembrar el usuario de prueba.
      await this.auth.seedTestUser();
      await this.auth.seedAdmin();
      await this.auth.seedSecondaryReviewer();
      // En una base nueva la evolución corre antes de crear el usuario demo.
      // Completar membresías después del seed evita un segundo reinicio.
      await this.dataSource.query(`
        INSERT INTO tfm_schema.project_memberships (project_id, user_id, role)
        SELECT p.id, u.id,
               CASE WHEN u.role = 'admin' THEN 'admin'
                    WHEN u.role IN ('curador', 'curator') THEN 'curator'
                    ELSE 'collaborator' END
        FROM tfm_schema.projects p CROSS JOIN tfm_schema.users u
        WHERE p.is_deleted = false AND u.is_deleted = false
        ON CONFLICT (project_id, user_id) DO NOTHING
      `);
    } catch (err) {
      this.logger.warn(`Bootstrap de BD no ejecutado: ${(err as Error).message}`);
    }
  }

  private resolveDdlPath(): string | null {
    const candidates = [
      this.config.get<string>('DDL_PATH'),
      join(process.cwd(), 'claude_workspace/architecture/ddl.sql'),
      join(process.cwd(), '../..', 'apps/api/claude_workspace/architecture/ddl.sql'),
      join(__dirname, '../../claude_workspace/architecture/ddl.sql'),
    ].filter(Boolean) as string[];
    return candidates.find((p) => existsSync(p)) ?? null;
  }

  private resolveEvolutionPath(): string | null {
    const candidates = [
      join(process.cwd(), 'claude_workspace/architecture/evolution_historia_viva.sql'),
      join(process.cwd(), '../..', 'apps/api/claude_workspace/architecture/evolution_historia_viva.sql'),
      join(__dirname, '../../claude_workspace/architecture/evolution_historia_viva.sql'),
    ];
    return candidates.find((p) => existsSync(p)) ?? null;
  }
}
