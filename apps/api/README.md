# API NestJS — Historia Viva Perú

Orquestador y fuente de verdad del producto. Gestiona autenticación, proyectos,
fuentes, procesamiento persistente, segmentos, entidades, revisiones, búsqueda,
publicación, datasets, modelos y auditoría.

## Dependencias externas

- PostgreSQL/pgvector; Neon en producción.
- Almacenamiento compatible con S3; Supabase Storage en producción.
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

## Cuota de fuentes de demostración

Con `DEMO_MODE=true`, `DEMO_MAX_SOURCES_PER_USER` limita las fuentes activas creadas
por cada cuenta de demostración (3 por defecto). Las cuentas con rol `admin`
están exentas de esta cuota tanto para PDF como para YouTube. El rol procede de
la cuenta activa en la base de datos, validada por JWT, no del cuerpo de la petición.

Para el uso de la autora, iniciar sesión con la cuenta administrativa configurada
por `ADMIN_USERNAME` (el Blueprint usa `administrador`) y su `ADMIN_PASSWORD`
privada. La cuenta pública `docente` conserva el rol `colaborador` y la cuota.
No cambiar `DEMO_MODE` para obtener la excepción. El límite de tamaño de PDF y
las restricciones del procesamiento público se gestionan por separado.

El cambio requiere desplegar la API en Render después de CI; no requiere volver
a publicar BETO ni modificar Modal. No cambia automáticamente roles de cuentas.

## Calidad

```powershell
npm test -- --runInBand
npm run build
npm run test:e2e
```

La suite unitaria verificada el 12 de septiembre de 2026 contiene 53 pruebas;
la compilación de la API también pasó. El smoke test de producción se
encuentra en [`../../scripts/smoke-deployment.ps1`](../../scripts/smoke-deployment.ps1).
