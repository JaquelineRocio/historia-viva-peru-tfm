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
