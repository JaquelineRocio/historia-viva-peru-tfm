import { createReadStream } from 'node:fs';
import { readdir, stat } from 'node:fs/promises';
import { relative, resolve, sep } from 'node:path';
import { PutObjectCommand, S3Client } from '@aws-sdk/client-s3';

const root = resolve(process.argv[2] || '../../artifacts/demo/files');
const required = ['R2_ENDPOINT', 'R2_BUCKET', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY'];
for (const key of required) if (!process.env[key]) throw new Error(`Falta ${key}`);

const client = new S3Client({
  region: process.env.R2_REGION || 'auto',
  endpoint: process.env.R2_ENDPOINT,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
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

for (const path of await files(root)) {
  const key = relative(root, path).split(sep).join('/');
  await client.send(new PutObjectCommand({ Bucket: process.env.R2_BUCKET, Key: key, Body: createReadStream(path) }));
  console.log(`R2 ${key}`);
}
