"""Fallback de transcripción con Whisper (para videos SIN subtítulos).

Cascada del TFM: youtube.py (subtítulos) → ESTE módulo (audio + Whisper).

Descarga el audio con yt-dlp y transcribe con faster-whisper (CTranslate2, CPU
con int8). Genera los mismos `TranscriptCue` que la vía de subtítulos, de modo
que el resto del pipeline (segmentación) es idéntico.

Dependencias PESADAS y opcionales: `faster-whisper` y `yt-dlp` (+ ffmpeg en el
sistema). Si no están instaladas, se lanza TranscriptError con instrucciones
claras, sin romper el arranque del servicio (import perezoso).
"""
from __future__ import annotations

import os
import tempfile

from app.config import settings
from app.transcription.youtube import (
    TranscriptCue,
    TranscriptResult,
    TranscriptError,
    extract_video_id,
)

# Caché del modelo Whisper (se carga una sola vez, es caro).
_whisper_model = None


def _load_model():
    """Carga perezosa del modelo faster-whisper (cacheado en memoria)."""
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise TranscriptError(
            "Fallback Whisper no disponible: falta 'faster-whisper'. "
            "Instala con: pip install faster-whisper (y ten ffmpeg en el PATH)."
        ) from exc

    _whisper_model = WhisperModel(
        settings.whisper_model,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )
    return _whisper_model


def _download_audio(video_id: str, dest_dir: str) -> str:
    """Descarga el audio del video con yt-dlp. Devuelve la ruta del archivo."""
    try:
        import yt_dlp
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise TranscriptError(
            "Fallback Whisper no disponible: falta 'yt-dlp'. "
            "Instala con: pip install yt-dlp."
        ) from exc

    out_tmpl = os.path.join(dest_dir, f"{video_id}.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_tmpl,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}
        ],
    }
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as exc:  # yt-dlp lanza tipos variados / bloqueos de red
        raise TranscriptError(f"No se pudo descargar el audio de {video_id}: {exc}") from exc

    audio_path = os.path.join(dest_dir, f"{video_id}.mp3")
    if not os.path.exists(audio_path):
        raise TranscriptError(f"Audio no encontrado tras la descarga de {video_id}")
    return audio_path


def transcribe_with_whisper(
    url_or_id: str,
    languages: list[str] | None = None,
) -> TranscriptResult:
    """Transcribe un video descargando su audio y aplicando Whisper.

    Devuelve un TranscriptResult (source='whisper') con cues por segmento de
    Whisper, cada uno con start/duration para conservar la navegación temporal.
    """
    video_id = extract_video_id(url_or_id)
    language = (languages[0] if languages else settings.whisper_language) or "es"

    model = _load_model()
    with tempfile.TemporaryDirectory() as tmp:
        audio_path = _download_audio(video_id, tmp)
        segments, _info = model.transcribe(
            audio_path,
            language=language,
            vad_filter=True,  # descarta silencios → mejores timestamps
        )
        cues = [
            TranscriptCue(
                start=round(float(seg.start), 3),
                duration=round(float(seg.end - seg.start), 3),
                text=seg.text.strip(),
            )
            for seg in segments
            if seg.text and seg.text.strip()
        ]

    if not cues:
        raise TranscriptError(f"Whisper no produjo texto para {video_id}")

    return TranscriptResult(
        video_id=video_id,
        language=language,
        source="whisper",
        is_generated=True,
        cues=cues,
    )
