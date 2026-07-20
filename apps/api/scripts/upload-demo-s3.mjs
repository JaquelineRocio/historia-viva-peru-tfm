import { createReadStream } from 'node:fs';
import { readdir, stat } from 'node:fs/promises';
import { relative, resolve, sep } from 'node:path';
import { PutObjectCommand, S3Client } from '@aws-sdk/client-s3';

const root = resolve(process.argv[2] || '../../artifacts/demo/files');
const required = ['S3_ENDPOINT', 'S3_BUCKET', 'S3_REGION', 'S3_ACCESS_KEY_ID', 'S3_SECRET_ACCESS_KEY'];
for (const key of required) {
  if (!process.env[key]?.trim()) throw new Error(`Falta ${key}`);
}

const value = (key) => process.env[key].trim();
const client = new S3Client({
  region: value('S3_REGION'),
  endpoint: value('S3_ENDPOINT'),
  forcePathStyle: true,
  credentials: {
    accessKeyId: value('S3_ACCESS_KEY_ID'),
    secretAccessKey: value('S3_SECRET_ACCESS_KEY'),
  },
});

async function files(directory) {
  const result = [];
  for (const name of await readdir(directory)) {
    const path = resolve(directory, name);
    if ((await stat(path)).isDirectory()) result.push(...await files(path));
    else result.push(path);
  }
  return result;
}

const paths = await files(root);
for (const path of paths) {
  const key = relative(root, path).split(sep).join('/');
  await client.send(new PutObjectCommand({
    Bucket: value('S3_BUCKET'),
    Key: key,
    Body: createReadStream(path),
    ContentType: 'application/pdf',
  }));
  console.log(`S3 ${key}`);
}
console.log(`Carga completa: ${paths.length} archivo(s)`);
