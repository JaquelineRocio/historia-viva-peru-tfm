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
import logging
import re
import tempfile
from pathlib import Path

from app.config import settings
from app.transcription.youtube import (
    TranscriptCue,
    TranscriptResult,
    TranscriptError,
    extract_video_id,
)

# Caché del modelo Whisper (se carga una sola vez, es caro).
_whisper_model = None
_logger = logging.getLogger(__name__)


class _DownloadLogger:
    """Diagnóstico de yt-dlp sin valores de cookies ni volcado de depuración."""

    def __init__(self, video_id: str):
        self.video_id = video_id
        self.cookies_loaded = False

    def _safe_message(self, message):
        message = str(message)
        if settings.youtube_cookies:
            raw = settings.youtube_cookies.get_secret_value()
            # También proteger configuraciones mal formadas y filas #HttpOnly_.
            secrets = [raw, raw.replace("\r\n", "\n")]
            for line in raw.splitlines():
                fields = line.split("\t", 6)
                if len(fields) == 7 and fields[6]:
                    secrets.append(fields[6])
            for secret in sorted(set(secrets), key=len, reverse=True):
                if secret:
                    message = message.replace(secret, "[REDACTED]")
        message = re.sub(r"\x1b\[[0-9;]*m", "", message)
        return message

    def _log(self, level, message):
        _logger.log(
            level, "yt-dlp video_id=%s cookies_configured=%s cookies_loaded=%s: %s",
            self.video_id, bool(settings.youtube_cookies), self.cookies_loaded,
            self._safe_message(message),
        )

    def debug(self, message):
        pass

    def warning(self, message):
        self._log(logging.WARNING, message)

    def error(self, message):
        self._log(logging.ERROR, message)


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
    download_logger = _DownloadLogger(video_id)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_tmpl,
        "quiet": True,
        "no_warnings": False,
        "logger": download_logger,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}
        ],
    }
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        # Una copia por descarga: yt-dlp puede modificarla al cerrar la sesión.
        # El contexto la elimina incluso si la descarga falla.
        with tempfile.TemporaryDirectory(prefix="youtube-auth-") as auth_dir:
            if settings.youtube_cookies:
                cookies = settings.youtube_cookies.get_secret_value().replace("\r\n", "\n")
                if not cookies.startswith(("# Netscape HTTP Cookie File", "# HTTP Cookie File")):
                    raise TranscriptError("La configuración de autenticación de YouTube no tiene formato Netscape.")
                cookie_path = Path(auth_dir) / "cookies.txt"
                cookie_path.write_text(cookies, encoding="utf-8")
                cookie_path.chmod(0o600)
                ydl_opts["cookiefile"] = str(cookie_path)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Forzar lectura de la cookie jar antes de marcarla como cargada.
                if "cookiefile" in ydl_opts:
                    download_logger.cookies_loaded = bool(list(ydl.cookiejar))
                    if not download_logger.cookies_loaded:
                        raise TranscriptError(
                            "ML_YOUTUBE_COOKIES está configurada, pero no contiene cookies legibles. "
                            "Exporta las cookies de youtube.com en formato Netscape y copia todo "
                            "el archivo, con sus filas y saltos de línea reales, al secreto de Modal."
                        )
                ydl.download([url])
    except TranscriptError as exc:
        download_logger.error(f"{type(exc).__name__}: {exc}")
        raise
    except Exception as exc:  # yt-dlp lanza tipos variados / bloqueos de red
        download_logger.error(f"{type(exc).__name__}: {exc}")
        if "sign in to confirm" in str(exc).lower():
            raise TranscriptError(
                "YouTube bloqueó la descarga del audio y solicita verificar la sesión. "
                "La administración debe revisar la autenticación de YouTube del servicio ML."
            ) from None
        raise TranscriptError(f"No se pudo descargar el audio de {video_id}. La descarga de YouTube falló.") from None

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

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = _download_audio(video_id, tmp)
        model = _load_model()
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
