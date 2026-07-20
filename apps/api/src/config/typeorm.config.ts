import { ConfigService } from '@nestjs/config';
import { TypeOrmModuleOptions } from '@nestjs/typeorm';

/**
 * Configuración de TypeORM.
 *
 * `synchronize: false` SIEMPRE: el esquema es propiedad de
 * `claude_workspace/architecture/ddl.sql` (fuente de verdad). TypeORM solo mapea.
 */
export function buildTypeOrmOptions(config: ConfigService): TypeOrmModuleOptions {
  const schema = config.get<string>('DB_SCHEMA', 'tfm_schema');
  const databaseUrl = config.get<string>('DATABASE_URL');
  const sslRequired = config.get<string>('PGSSLMODE') === 'require' || databaseUrl?.includes('sslmode=require');
  return {
    type: 'postgres',
    ...(databaseUrl ? { url: databaseUrl } : {
      host: config.get<string>('PGHOST', 'localhost'),
      port: parseInt(config.get<string>('PGPORT', '5432'), 10),
      username: config.get<string>('PGUSER', 'tfm'),
      password: config.get<string>('PGPASSWORD', 'tfm'),
      database: config.get<string>('PGDATABASE', 'tfm'),
    }),
    ...(sslRequired ? { ssl: { rejectUnauthorized: false } } : {}),
    schema,
    autoLoadEntities: true,
    synchronize: false,
    logging: config.get<string>('NODE_ENV') !== 'production' ? ['error', 'warn'] : ['error'],
  };
}
