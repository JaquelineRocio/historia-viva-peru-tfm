import { readFile } from 'node:fs/promises';
import { gunzipSync } from 'node:zlib';
import pg from 'pg';

const { Client } = pg;
const input = process.argv.find((arg) => arg.endsWith('.sql') || arg.endsWith('.sql.gz'))
  ?? 'artifacts/demo/demo-seed.sql.gz';
const confirmed = process.argv.includes('--confirm-replace-demo');
const databaseUrl = process.env.NEON_DATABASE_URL?.trim() || process.env.DATABASE_URL?.trim();

if (!confirmed) {
  throw new Error('Falta --confirm-replace-demo. La importacion reemplaza los datos demo, pero conserva usuarios.');
}
if (!databaseUrl) {
  throw new Error('Define NEON_DATABASE_URL con la conexion directa de Neon.');
}

const compressed = await readFile(input);
let sql = input.endsWith('.gz') ? gunzipSync(compressed).toString('utf8') : compressed.toString('utf8');

// Las ordenes con barra pertenecen al cliente psql, no al protocolo PostgreSQL.
sql = sql.replace(/^\\(?:un)?restrict\b.*$/gm, '');
// El dump se genero con --disable-triggers. Neon no concede privilegios de
// superusuario para desactivar triggers internos; pg_dump ya ordena los datos
// por dependencias para este corpus y no existen ciclos en sus filas demo.
sql = sql.replace(/^ALTER TABLE .+ (?:DISABLE|ENABLE) TRIGGER ALL;\s*$/gm, '');
// Compatibilidad con el export previo al proveedor S3 generico.
sql = sql.replace(/'r2'/g, "'s3'");

function splitStatements(source) {
  const statements = [];
  let start = 0;
  let single = false;
  let singleEscape = false;
  let double = false;
  let lineComment = false;
  let blockComment = false;
  let dollarTag = null;

  for (let i = 0; i < source.length; i += 1) {
    const char = source[i];
    const next = source[i + 1];

    if (lineComment) {
      if (char === '\n') lineComment = false;
      continue;
    }
    if (blockComment) {
      if (char === '*' && next === '/') {
        blockComment = false;
        i += 1;
      }
      continue;
    }
    if (dollarTag) {
      if (source.startsWith(dollarTag, i)) {
        i += dollarTag.length - 1;
        dollarTag = null;
      }
      continue;
    }
    if (single) {
      if (singleEscape && char === '\\') {
        i += 1;
      } else if (char === "'" && next === "'") {
        i += 1;
      } else if (char === "'") {
        single = false;
        singleEscape = false;
      }
      continue;
    }
    if (double) {
      if (char === '"' && next === '"') {
        i += 1;
      } else if (char === '"') {
        double = false;
      }
      continue;
    }

    if (char === '-' && next === '-') {
      lineComment = true;
      i += 1;
    } else if (char === '/' && next === '*') {
      blockComment = true;
      i += 1;
    } else if (char === "'") {
      single = true;
      const prefix = source[i - 1];
      const beforePrefix = source[i - 2];
      singleEscape = (prefix === 'E' || prefix === 'e')
        && (!beforePrefix || !/[A-Za-z0-9_$]/.test(beforePrefix));
    } else if (char === '"') {
      double = true;
    } else if (char === '$') {
      const match = source.slice(i).match(/^\$[A-Za-z_][A-Za-z0-9_]*\$|^\$\$/);
      if (match) {
        dollarTag = match[0];
        i += dollarTag.length - 1;
      }
    } else if (char === ';') {
      const statement = source.slice(start, i + 1).trim();
      if (statement) statements.push(statement);
      start = i + 1;
    }
  }

  const remainder = source.slice(start).trim();
  if (remainder) statements.push(remainder);
  return statements;
}

function createBatches(statements, maxBytes = 1024 * 1024) {
  const batches = [];
  let current = [];
  let bytes = 0;
  for (const statement of statements) {
    const statementBytes = Buffer.byteLength(statement, 'utf8') + 1;
    if (current.length && bytes + statementBytes > maxBytes) {
      batches.push(current.join('\n'));
      current = [];
      bytes = 0;
    }
    current.push(statement);
    bytes += statementBytes;
  }
  if (current.length) batches.push(current.join('\n'));
  return batches;
}

const normalizedUrl = new URL(databaseUrl);
if (normalizedUrl.searchParams.get('sslmode') === 'require') {
  normalizedUrl.searchParams.set('sslmode', 'verify-full');
}
const statements = splitStatements(sql);
const batches = createBatches(statements);
console.log(`Seed preparado: ${statements.length} sentencias en ${batches.length} lotes.`);

const client = new Client({
  connectionString: normalizedUrl.toString(),
  connectionTimeoutMillis: 30000,
  keepAlive: true,
  keepAliveInitialDelayMillis: 10000,
});
client.on('error', (error) => console.error(`Conexion Neon interrumpida: ${error.message}`));
await client.connect();

try {
  console.log('Limpiando los datos demo anteriores...');
  await client.query('BEGIN');
  await client.query(`
    DO $$
    DECLARE names text;
    BEGIN
      SELECT string_agg(format('tfm_schema.%I', table_name), ', ')
      INTO names
      FROM information_schema.tables
      WHERE table_schema = 'tfm_schema'
        AND table_type = 'BASE TABLE'
        AND table_name <> 'users';
      IF names IS NOT NULL THEN
        EXECUTE 'TRUNCATE TABLE ' || names || ' RESTART IDENTITY CASCADE';
      END IF;
    END $$;
  `);
  console.log('Importando datos...');
  for (let index = 0; index < batches.length; index += 1) {
    await client.query(batches[index]);
    if ((index + 1) % 10 === 0 || index === batches.length - 1) {
      console.log(`Progreso: ${index + 1}/${batches.length} lotes.`);
    }
  }
  console.log('Restaurando membresias...');
  await client.query(`
    INSERT INTO tfm_schema.project_memberships(project_id, user_id, role)
    SELECT p.id, u.id,
      CASE WHEN u.role = 'admin' THEN 'admin' ELSE 'collaborator' END
    FROM tfm_schema.projects p CROSS JOIN tfm_schema.users u
    WHERE p.is_deleted = false AND u.is_deleted = false
    ON CONFLICT (project_id, user_id) DO NOTHING;
  `);
  await client.query('COMMIT');

  const { rows } = await client.query(`
    SELECT
      (SELECT count(*)::int FROM tfm_schema.projects) AS projects,
      (SELECT count(*)::int FROM tfm_schema.resources) AS resources,
      (SELECT count(*)::int FROM tfm_schema.resource_segments) AS segments,
      (SELECT count(*)::int FROM tfm_schema.users WHERE is_deleted = false) AS users;
  `);
  console.log('Demo importada correctamente:', rows[0]);
} catch (error) {
  await client.query('ROLLBACK');
  throw error;
} finally {
  await client.end();
}
