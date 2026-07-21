import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { GetObjectCommand, PutObjectCommand, S3Client } from '@aws-sdk/client-s3';
import { access, mkdir, readFile, writeFile } from 'node:fs/promises';
import { join, resolve, sep } from 'node:path';

export type StorageProvider = 'local' | 's3';

export interface StoredFile {
  provider: StorageProvider;
  key: string;
  legacyPath?: string;
}

/**
 * Almacenamiento de documentos con dos drivers compatibles:
 * - local: Docker/desarrollo, bajo UPLOAD_ROOT;
 * - s3: proveedor compatible con S3 (Supabase Storage en producción).
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
    this.provider = driver === 's3' ? 's3' : 'local';
    this.uploadRoot = resolve(this.config.get<string>('UPLOAD_ROOT', join(process.cwd(), 'storage', 'uploads')));

    if (this.provider === 's3') {
      const endpoint = this.required('S3_ENDPOINT');
      this.bucket = this.required('S3_BUCKET');
      this.s3 = new S3Client({
        region: this.config.get<string>('S3_REGION', 'us-west-2'),
        endpoint,
        forcePathStyle: true,
        credentials: {
          accessKeyId: this.required('S3_ACCESS_KEY_ID'),
          secretAccessKey: this.required('S3_SECRET_ACCESS_KEY'),
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
    if (resolvedProvider === 's3') {
      if (!key) throw new Error('La fuente no tiene clave de almacenamiento');
      const response = await this.s3!.send(new GetObjectCommand({ Bucket: this.bucket!, Key: this.safeKey(key) }));
      if (!response.Body) throw new Error('El archivo no está disponible en el almacenamiento S3');
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
    if (!value) throw new Error(`Falta la variable obligatoria ${key} para almacenamiento S3`);
    return value;
  }

}
