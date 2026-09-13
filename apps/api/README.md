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


### Protecci?n del procesamiento p?blico

`PUBLIC_PROCESS_MAX_PER_MINUTE` (defecto 1) limita globalmente los intentos
admitidos antes de consultar metadatos ML. `PUBLIC_PROCESS_MAX_PENDING` (defecto 2)
rechaza altas p?blicas cuando los trabajos queued/processing alcanzan ese tama?o.
La admisi?n se serializa en PostgreSQL entre sesiones e instancias. La saturaci?n
y los fallos de inspecci?n devuelven 503 con mensaje p?blico; explorar ejemplos
existentes no consume estas cuotas. Los l?mites por sesi?n/IP siguen vigentes.
Estos controles no sustituyen una prueba de carga ni son un l?mite global de
concurrencia para trabajos docentes. No se ha ejecutado carga contra producci?n.


### Inicio de sesi?n en la demo

La interfaz `/explorar` requiere inicio de sesi?n y vuelve a esa ruta tras entrar.
`POST /api/public/explore/process` y `GET /api/public/explore/process/:id` requieren
`Authorization: Bearer <JWT>` v?lido y una cuenta activa. Aunque conservan el
prefijo public por compatibilidad de URL, estas dos operaciones son privadas.
El servidor deriva la identidad para cuota y consulta del usuario autenticado;
`X-Demo-Session` ya no se utiliza. Los resultados de nuevas solicitudes solo se
consultan con la cuenta que las cre?. Las solicitudes an?nimas anteriores no se
reasignan a cuentas; sus tokens de sesi?n antiguos dejan de funcionar.
El cat?logo de ejemplos aprobados conserva acceso p?blico por API.
Desplegar API y frontend juntos; el frontend anterior no env?a JWT en estas rutas.
Las cuotas globales y por IP se conservan; la cuota por sesi?n ahora es por cuenta.
