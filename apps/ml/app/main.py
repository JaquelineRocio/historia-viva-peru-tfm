"""Servicio ML (FastAPI) — capa de cómputo del TFM.

Responsabilidades: transcripción, segmentación, entrenamiento BETO, inferencia y
métricas. NestJS es el orquestador y dueño de la BD; este servicio es cómputo puro
invocado por HTTP (MlServicePort → HttpMlAdapter).
"""
import threading
import uuid
from typing import Dict, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.config import resolve_storage_path, settings
from app.transcription.youtube import fetch_transcript, TranscriptError
from app.transcription.supadata import fetch_supadata_transcript
from app.transcription.whisper import transcribe_with_whisper
from app.segmentation import segment_by_time
from app.ml import jobs as jobs_registry

app = FastAPI(
    title="TFM ML Service",
    description="Transcripción, segmentación, entrenamiento BETO e inferencia.",
    version="0.1.0",
)

_model_bootstrap = {"status": "disabled", "error": None, "repo": settings.default_model_repo}


def _load_default_model() -> None:
    if not settings.default_model_repo:
        return
    _model_bootstrap["status"] = "loading"
    try:
        from huggingface_hub import snapshot_download
        from app.ml import beto

        target = resolve_storage_path(settings.default_model_path)
        target.mkdir(parents=True, exist_ok=True)
        snapshot_download(repo_id=settings.default_model_repo, local_dir=str(target))
        beto.load_model(str(target))
        _model_bootstrap["status"] = "ready"
    except Exception as exc:  # health expone el detalle sin impedir que el Space arranque
        _model_bootstrap["status"] = "error"
        _model_bootstrap["error"] = str(exc)


@app.on_event("startup")
def bootstrap_default_model() -> None:
    if settings.default_model_repo:
        threading.Thread(target=_load_default_model, name="default-model-loader", daemon=True).start()


def require_internal_token(x_internal_token: Optional[str] = Header(default=None)) -> None:
    """Auth interna NestJS→ML: si ML_INTERNAL_TOKEN está definido, exige el header.

    `/health` queda exento (lo usan los healthchecks de la plataforma de deploy).
    """
    if settings.internal_token and x_internal_token != settings.internal_token:
        raise HTTPException(status_code=401, detail="Token interno inválido o ausente")


PROTECTED = [Depends(require_internal_token)]


# ----------------------------- Schemas ---------------------------------------
class TranscribeRequest(BaseModel):
    youtube_url: str = Field(..., description="URL o ID de un video de YouTube")
    languages: Optional[List[str]] = Field(default=None, description="Idiomas preferidos")


class SegmentRequest(BaseModel):
    cues: List[dict] = Field(..., description="Cues [{start, duration|end, text}]")
    window_sec: float = 60.0
    overlap_sec: float = 10.0


class TrainRequest(BaseModel):
    version_tag: str
    labels: List[str]
    items: List[dict] = Field(..., description="[{text, label, split}]")
    base_model: str
    hyperparams: Optional[Dict] = None
    output_dir: str


class LoadModelRequest(BaseModel):
    artifact_path: str


class InferRequest(BaseModel):
    texts: List[str]


class EmbeddingRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, max_length=64)


class EntityRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, max_length=32)


# ----------------------------- Endpoints -------------------------------------
@app.get("/health")
def health() -> dict:
    from app.ml import beto, embeddings, entities

    return {
        "status": "ok",
        "service": "ml",
        "version": app.version,
        "components": {
            "beto": {"ready": beto.is_loaded(), **_model_bootstrap},
            "embeddings": {"ready": embeddings.is_loaded(), "model": settings.embedding_model},
            "ner": {"ready": entities.is_loaded(), "model": settings.ner_model},
        },
    }


@app.post("/transcribe", dependencies=PROTECTED)
def transcribe(req: TranscribeRequest) -> dict:
    """Transcripción vía subtítulos de YouTube (422 → NestJS activa el fallback Whisper)."""
    try:
        result = fetch_transcript(req.youtube_url, req.languages)
    except TranscriptError as youtube_exc:
        if settings.supadata_api_key:
            try:
                result = fetch_supadata_transcript(
                    req.youtube_url,
                    settings.supadata_api_key,
                    req.languages,
                )
            except TranscriptError as provider_exc:
                detail = f"{youtube_exc} Proveedor alternativo: {provider_exc}"
                raise HTTPException(status_code=422, detail=detail) from provider_exc
        else:
            # 422 → NestJS decide activar el fallback Whisper.
            raise HTTPException(status_code=422, detail=str(youtube_exc)) from youtube_exc
    return result.to_dict()


@app.post("/transcribe/audio", dependencies=PROTECTED)
def transcribe_audio(req: TranscribeRequest) -> dict:
    """Fallback Whisper: descarga audio y transcribe (lento; sin subtítulos).

    Invocado por NestJS cuando /transcribe devuelve 422. Requiere faster-whisper
    + yt-dlp + ffmpeg; si faltan, devuelve 422 con instrucciones.
    """
    try:
        result = transcribe_with_whisper(req.youtube_url, req.languages)
    except TranscriptError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result.to_dict()


@app.post("/segment", dependencies=PROTECTED)
def segment(req: SegmentRequest) -> dict:
    """Segmenta cues en ventanas temporales con solape."""
    try:
        segments = segment_by_time(req.cues, req.window_sec, req.overlap_sec)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"count": len(segments), "segments": [s.to_dict() for s in segments]}


@app.post('/documents/pdf/extract', dependencies=PROTECTED)
async def extract_pdf_document(file: UploadFile = File(...)) -> dict:
    from app.documents.pdf import extract_pdf

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail='El PDF supera el límite de 50 MB')
    try:
        return extract_pdf(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ----------------------------- Entrenamiento / Inferencia --------------------
@app.post("/train", dependencies=PROTECTED)
def train(req: TrainRequest, background_tasks: BackgroundTasks) -> dict:
    """Lanza el fine-tuning de BETO en segundo plano. Devuelve el job_id."""
    from app.ml.trainer import train_job

    try:
        resolve_storage_path(req.output_dir)  # valida path traversal antes de encolar
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = str(uuid.uuid4())
    jobs_registry.create_job(job_id)
    background_tasks.add_task(train_job, job_id, req.dict())
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}", dependencies=PROTECTED)
def job_status(job_id: str) -> dict:
    job = jobs_registry.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return job


@app.post("/models/load", dependencies=PROTECTED)
def models_load(req: LoadModelRequest) -> dict:
    """Carga un artefacto de modelo como modelo activo en memoria."""
    from app.ml import beto

    try:
        artifact_path = str(resolve_storage_path(req.artifact_path))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        labels = beto.load_model(artifact_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ImportError as exc:
        raise HTTPException(status_code=422, detail=f"Faltan deps ML: {exc}") from exc
    return {"loaded": True, "labels": labels}


@app.post("/infer", dependencies=PROTECTED)
def infer(req: InferRequest) -> dict:
    """Clasifica textos con el modelo activo."""
    from app.ml import beto

    if not beto.is_loaded():
        raise HTTPException(status_code=409, detail="No hay modelo activo cargado")
    return {"predictions": beto.infer(req.texts)}


@app.post("/embeddings", dependencies=PROTECTED)
def embeddings(req: EmbeddingRequest) -> dict:
    """Genera vectores normalizados para búsqueda semántica en español."""
    from app.ml.embeddings import encode

    try:
        vectors = encode(req.texts)
    except (ImportError, OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"Embeddings no disponibles: {exc}") from exc
    return {"model": settings.embedding_model, "dimensions": 384, "embeddings": vectors}


@app.post("/entities/extract", dependencies=PROTECTED)
def extract_entities(req: EntityRequest) -> dict:
    """Extrae personas, lugares, organizaciones, fechas y periodos."""
    from app.ml.entities import extract

    return extract(req.texts)
