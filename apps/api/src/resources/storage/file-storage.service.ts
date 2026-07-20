import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { GetObjectCommand, PutObjectCommand, S3Client } from '@aws-sdk/client-s3';
import { access, mkdir, readFile, writeFile } from 'node:fs/promises';
import { join, resolve, sep } from 'node:path';

export type StorageProvider = 'local' | 's3' | 'r2';

export interface StoredFile {
  provider: StorageProvider;
  key: string;
  legacyPath?: string;
}

/**
 * Almacenamiento de documentos con dos drivers compatibles:
 * - local: Docker/desarrollo, bajo UPLOAD_ROOT;
 * - s3: proveedor compatible con S3 (Cloudflare R2 en producción).
 * - r2: identificador heredado para recursos existentes.
 *
 * Los documentos del MVP están limitados a 50 MB, por lo que devolver Buffer
 * mantiene sencilla y auditable la integración con extracción PDF y descarga.
 */
@Injectable()
export class FileStorageService {
  private readonly provider: StorageProvider;
  private readonly uploadRoot: string;
  private readonly bucket?: string;
  private readonly s3?: S3Client;

  constructor(private readonly config: ConfigService) {
    const driver = this.config.get<string>('FILE_STORAGE_DRIVER', 'local');
    this.provider = driver === 's3' || driver === 'r2' ? 's3' : 'local';
    this.uploadRoot = resolve(this.config.get<string>('UPLOAD_ROOT', join(process.cwd(), 'storage', 'uploads')));

    if (this.provider === 's3') {
      const endpoint = this.requiredAny('S3_ENDPOINT', 'R2_ENDPOINT');
      this.bucket = this.requiredAny('S3_BUCKET', 'R2_BUCKET');
      this.s3 = new S3Client({
        region: this.config.get<string>('S3_REGION') || this.config.get<string>('R2_REGION', 'auto'),
        endpoint,
        forcePathStyle: true,
        credentials: {
          accessKeyId: this.requiredAny('S3_ACCESS_KEY_ID', 'R2_ACCESS_KEY_ID'),
          secretAccessKey: this.requiredAny('S3_SECRET_ACCESS_KEY', 'R2_SECRET_ACCESS_KEY'),
        },
      });
    }
  }

  activeProvider(): StorageProvider {
    return this.provider;
  }

  async put(key: string, content: Buffer, contentType: string): Promise<StoredFile> {
    const safeKey = this.safeKey(key);
    if (this.provider === 's3') {
      await this.s3!.send(new PutObjectCommand({
        Bucket: this.bucket!,
        Key: safeKey,
        Body: content,
        ContentType: contentType,
      }));
      return { provider: 's3', key: safeKey };
    }

    const path = this.localPath(safeKey);
    await mkdir(resolve(path, '..'), { recursive: true });
    await writeFile(path, content);
    return { provider: 'local', key: safeKey, legacyPath: path };
  }

  async get(provider: StorageProvider | null | undefined, key?: string | null, legacyPath?: string | null): Promise<Buffer> {
    const resolvedProvider = provider || (legacyPath ? 'local' : this.provider);
    if (resolvedProvider === 's3' || resolvedProvider === 'r2') {
      if (!key) throw new Error('La fuente no tiene clave de almacenamiento');
      const response = await this.s3!.send(new GetObjectCommand({ Bucket: this.bucket!, Key: this.safeKey(key) }));
      if (!response.Body) throw new Error('El archivo no está disponible en R2');
      return Buffer.from(await response.Body.transformToByteArray());
    }

    const path = legacyPath ? this.validLegacyPath(legacyPath) : this.localPath(this.safeKey(key || ''));
    await access(path);
    return readFile(path);
  }

  private localPath(key: string): string {
    const path = resolve(this.uploadRoot, key);
    if (!path.startsWith(`${this.uploadRoot}${sep}`)) throw new Error('Ruta de documento no permitida');
    return path;
  }

  private validLegacyPath(pathValue: string): string {
    const path = resolve(pathValue);
    if (!path.startsWith(`${this.uploadRoot}${sep}`)) throw new Error('Ruta de documento no permitida');
    return path;
  }

  private safeKey(key: string): string {
    const normalized = key.replace(/\\/g, '/').replace(/^\/+/, '');
    if (!normalized || normalized.split('/').some((part) => !part || part === '.' || part === '..')) {
      throw new Error('Clave de almacenamiento no permitida');
    }
    return normalized;
  }

  private required(key: string): string {
    const value = this.config.get<string>(key);
    if (!value) throw new Error(`Falta la variable obligatoria ${key} para almacenamiento R2`);
    return value;
  }

  private requiredAny(primary: string, legacy: string): string {
    const value = this.config.get<string>(primary) || this.config.get<string>(legacy);
    if (!value) throw new Error(`Falta la variable obligatoria ${primary} para almacenamiento S3`);
    return value;
  }
}
