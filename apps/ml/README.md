# Servicio ML — Historia Viva Perú

Servicio FastAPI de cómputo para segmentación, extracción PDF, transcripción,
embeddings, NER e inferencia BETO. En producción se ejecuta en **Modal**; Hugging
Face Hub almacena `Jaqueline98/historia-viva-beto-v1`.

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

Estado verificado: **24 pruebas superadas**. BETO v1 alcanza F1 macro 0.425 y
permanece como modelo experimental.
