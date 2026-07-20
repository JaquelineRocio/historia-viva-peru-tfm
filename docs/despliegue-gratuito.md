# Despliegue gratuito del TFM

## 1. Hugging Face Hub — modelo

1. Cree un repositorio público de modelo, por ejemplo `usuario/historia-viva-beto-v1`.
2. Copie los archivos extraídos de `modelo_Vn.zip` y la ficha
   `deploy/huggingface-model/README.md`.
3. No suba el ZIP a GitHub: supera el límite de 100 MB por objeto.
4. Compruebe que `config.json`, tokenizer y pesos puedan descargarse con
   `snapshot_download`.

## 2. Modal Starter — servicio ML

Hugging Face Spaces con Docker o Gradio requieren actualmente un plan pagado.
La demo usa Modal Starter, que proporciona una URL HTTPS estable y escala a cero:

```powershell
python -m modal deploy apps/ml/modal_app.py
```

Use la URL `modal.run` resultante como `ML_SERVICE_URL` en Render. Configure
también `ML_INTERNAL_TOKEN`, `MODAL_PROXY_TOKEN_ID` y
`MODAL_PROXY_TOKEN_SECRET`. Consulte `docs/modal-paso-a-paso.md`.

## 3. Neon — PostgreSQL + pgvector

1. Cree un proyecto PostgreSQL gratuito.
2. Copie la connection string y mantenga `sslmode=require`.
3. No ejecute manualmente el DDL: la API aplica `ddl.sql` y las evoluciones de
   forma idempotente al arrancar.
4. Importe la demo solo después del primer arranque de la API.

## 4. Cloudflare R2 — archivos

1. Cree un bucket privado `historia-viva`.
2. Cree un token con lectura/escritura limitado a ese bucket.
3. Anote endpoint S3, access key y secret.
4. Exporte los datos locales y archivos:

```powershell
./scripts/demo/export-demo.ps1
```

5. Suba los archivos preparados:

```powershell
$env:R2_ENDPOINT='https://ACCOUNT.r2.cloudflarestorage.com'
$env:R2_BUCKET='historia-viva'
$env:R2_ACCESS_KEY_ID='...'
$env:R2_SECRET_ACCESS_KEY='...'
node apps/api/scripts/upload-demo-r2.mjs artifacts/demo/files
```

No habilite acceso público directo al bucket. La API controla archivos privados y
solo sirve fuentes aprobadas en la ruta pública.

## 5. Render — API

1. Cree un Blueprint desde `render.yaml`.
2. Complete todas las variables con `sync: false`:
   - `DATABASE_URL` de Neon.
   - `WEB_ORIGIN` con la URL definitiva de Vercel.
   - `ADMIN_PASSWORD` aleatoria y privada.
   - credenciales R2.
   - `ML_SERVICE_URL` de Modal.
   - `ML_INTERNAL_TOKEN` compartido con Modal.
   - `MODAL_PROXY_TOKEN_ID` y `MODAL_PROXY_TOKEN_SECRET`.
3. Confirme que `/api/health` responde.
4. Importe el seed sanitizado en la base recién creada. Si usa el contenedor local
   como cliente PostgreSQL, adapte `DATABASE_URL`; nunca importe sobre datos reales
   sin copia de seguridad.

La cola `database` conserva ejecuciones pendientes en PostgreSQL y las recupera
tras un reinicio. Render no almacena PDF ni modelos localmente.

## 6. Vercel — React

1. Importe el repositorio con root directory `apps/web`.
2. Defina `VITE_API_URL=https://SU-API.onrender.com/api`.
3. Publique y copie el dominio en `WEB_ORIGIN` de Render.
4. Vuelva a desplegar la API para aplicar CORS.

## 7. Validación final

```powershell
./scripts/smoke-deployment.ps1 -ApiUrl https://SU-API.onrender.com
```

Después complete las cuatro URL pendientes del README y pruebe desde una ventana
privada. Los niveles gratuitos pueden tardar al despertar; eso debe indicarse en
la defensa.

Referencias: [Render Free](https://render.com/docs/free),
[Neon](https://neon.com/pricing), [R2](https://developers.cloudflare.com/r2/pricing/),
[condiciones actuales de Hugging Face Spaces](https://huggingface.co/spaces/launch),
[precios de Modal](https://modal.com/pricing) y
[límites de GitHub](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits).
