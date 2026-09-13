# Servicio ML — Historia Viva Perú

Servicio FastAPI de cómputo para segmentación, extracción PDF, transcripción,
embeddings, NER e inferencia BETO. En producción se ejecuta en **Modal**; Hugging
Face Hub almacena los pesos. `configs/production-model.json` fija la revisión y
los hashes de la versión que debe servir Modal.

## Flujo de YouTube

1. `youtube-transcript-api` intenta obtener subtítulos nativos.
2. Supadata actúa como proveedor alternativo ante bloqueos de IP.
3. NestJS invoca `yt-dlp` + `faster-whisper` como último fallback.

Supadata requiere `ML_SUPADATA_API_KEY`. Los endpoints privados exigen
`ML_INTERNAL_TOKEN`; Modal añade además autenticación mediante Proxy Token.

### YouTube solicita verificar que no eres un bot

Si falla `transcribeAudio` con `Sign in to confirm`, YouTube está rechazando la
descarga desde el servicio ML. Render solo transmite el error; la descarga ocurre
en Modal. El cambio SQL de seguimiento de estados no resuelve este bloqueo.

El fallback de audio admite `ML_YOUTUBE_COOKIES`: contenido completo de un archivo
de cookies de YouTube en formato Netscape, con saltos de línea reales (no una ruta,
JSON ni el texto literal `\n`). Para configurarlo:

1. Exportar únicamente las cookies de YouTube siguiendo la
   [guía oficial de yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies).
   Las cookies permiten usar la sesión: no enviarlas por chat ni subirlas a Git.
   yt-dlp advierte que la cuenta puede sufrir un bloqueo temporal o permanente.
2. En Modal, editar el secreto existente `historia-viva-ml` y añadir
   `ML_YOUTUBE_COOKIES` con ese contenido, conservando las claves existentes.
   No configurarlo en Vercel ni en la API de Render.
3. Publicar el cambio de código y desplegar ML mediante el flujo habitual para
   que los nuevos contenedores lean el secreto. Después, reintentar la fuente.

Cada descarga usa una copia temporal privada, eliminada al terminar o fallar.
Sin la variable se mantiene la descarga anónima. La autenticación no garantiza
acceso: YouTube puede rechazar la IP, caducar la sesión o exigir otros mecanismos.
No se han probado cookies reales ni la descarga remota con esta configuración.
Los logs del servicio ML registran advertencias y errores originales de yt-dlp,
ocultando el contenido configurado y los valores de las cookies. Cada entrada
incluye `video_id`, `cookies_configured` y `cookies_loaded`. Este último indica
que yt-dlp leyó una cookie jar no vacía, no que YouTube aceptara la sesión.
El mensaje simplificado de la interfaz se conserva. Para incorporar estos logs
hay que publicar y desplegar el código actualizado; reiniciar la versión anterior
no añade esta funcionalidad.
El proveedor Supadata existente usa solo subtítulos nativos y requiere su propia
clave; no garantiza una transcripción para videos sin subtítulos.

## Ejecución local

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt -r requirements-ml.txt
.venv\Scripts\python run.py
```

## Pruebas y despliegue

```powershell
.venv\Scripts\python -m pytest -q
python -m modal deploy modal_app.py
```

Publicación y despliegue automático: [guía de modelos](../../docs/aprendizaje/despliegue-modelo-automatico.md).
El comando local `scripts/publish_model.py publish` prepara, verifica y publica
los pesos; el push de la selección a `main` activa CI y el despliegue en Modal.
La configuración inicial conserva v1 hasta publicar y seleccionar R2.

Estado verificado el 12 de septiembre de 2026: **76 pruebas ML superadas**, más
paridad de inferencia del paquete real R2 en cinco textos sintéticos. R2 tiene
F1 macro registrado de 0,532392 en V; sigue siendo experimental. Esta verificación
local no acredita una publicación ni un despliegue remoto.
