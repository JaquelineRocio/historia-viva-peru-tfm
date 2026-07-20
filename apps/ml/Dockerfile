# Servicio ML (FastAPI). Torch CPU-only wheel para reducir tamaño (Día 4).
FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema para audio (Whisper, Día 2)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir torch==2.12.0 --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
