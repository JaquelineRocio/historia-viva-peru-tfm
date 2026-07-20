# API NestJS — Historia Viva Perú

Orquestador y fuente de verdad del producto. Gestiona autenticación, proyectos,
fuentes, procesamiento persistente, segmentos, entidades, revisiones, búsqueda,
publicación, datasets, modelos y auditoría.

## Dependencias externas

- PostgreSQL/pgvector; Neon en producción.
- Almacenamiento compatible con S3; Cloudflare R2 en producción.
- Servicio FastAPI protegido; Modal en producción.
- Redis/BullMQ solo como opción local. Render usa la cola persistida en base de
  datos (`PROCESSING_QUEUE_DRIVER=database`).

## Ejecución

```powershell
npm ci
npm run start:dev
```

Swagger: `http://localhost:3000/api/docs`.

Las variables se documentan en [`.env.example`](.env.example). Nunca publique
`DATABASE_URL`, secretos JWT, credenciales S3, tokens de Modal ni claves de
Supadata.

## Calidad

```powershell
npm test -- --runInBand
npm run build
npm run test:e2e
```

La suite unitaria verificada contiene 14 pruebas. El smoke test de producción se
encuentra en [`../../scripts/smoke-deployment.ps1`](../../scripts/smoke-deployment.ps1).
