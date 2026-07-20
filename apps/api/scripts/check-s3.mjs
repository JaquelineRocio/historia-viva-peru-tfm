import { HeadBucketCommand, S3Client } from '@aws-sdk/client-s3';

const required = ['S3_ENDPOINT', 'S3_BUCKET', 'S3_REGION', 'S3_ACCESS_KEY_ID', 'S3_SECRET_ACCESS_KEY'];
for (const key of required) {
  if (!process.env[key]) throw new Error(`Falta ${key}`);
}

const client = new S3Client({
  region: process.env.S3_REGION,
  endpoint: process.env.S3_ENDPOINT,
  forcePathStyle: true,
  credentials: {
    accessKeyId: process.env.S3_ACCESS_KEY_ID,
    secretAccessKey: process.env.S3_SECRET_ACCESS_KEY,
  },
});

await client.send(new HeadBucketCommand({ Bucket: process.env.S3_BUCKET }));
console.log(`S3 OK: acceso confirmado al bucket ${process.env.S3_BUCKET}`);
