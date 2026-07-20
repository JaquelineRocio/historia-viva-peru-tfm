"""Transcripción vía subtítulos de YouTube (rápida, gratuita, con timestamps).

Estrategia en cascada del TFM:
  1) youtube-transcript-api  (este módulo) — subtítulos ES manuales o autogenerados.
  2) fallback Whisper        (Día 2, whisper.py) — descarga audio y transcribe.

Usa la API v1.x (basada en instancia): YouTubeTranscriptApi().list()/.fetch().
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from app.config import settings

_YT_ID_PATTERNS = [
    r"(?:v=|\/videos\/|embed\/|youtu\.be\/|\/v\/|watch\?v=|&v=)([A-Za-z0-9_-]{11})",
    r"^([A-Za-z0-9_-]{11})$",  # ya es un id
]


class TranscriptError(Exception):
    """Error de dominio para fallos de transcripción (mapeable a HTTP 4xx)."""


@dataclass
class TranscriptCue:
    """Un fragmento crudo de subtítulo con su timestamp."""
    start: float          # segundos
    duration: float       # segundos
    text: str

    @property
    def end(self) -> float:
        return round(self.start + self.duration, 3)


@dataclass
class TranscriptResult:
    video_id: str
    language: str
    source: str           # "api" | "whisper"
    is_generated: bool
    cues: list[TranscriptCue]

    def to_dict(self) -> dict:
        return {
            "video_id": self.video_id,
            "language": self.language,
            "source": self.source,
            "is_generated": self.is_generated,
            "cue_count": len(self.cues),
            "full_text": " ".join(c.text for c in self.cues),
            "cues": [asdict(c) for c in self.cues],
        }


def extract_video_id(url_or_id: str) -> str:
    """Extrae el ID de 11 caracteres de una URL de YouTube (o lo devuelve si ya es un ID)."""
    url_or_id = url_or_id.strip()
    for pattern in _YT_ID_PATTERNS:
        m = re.search(pattern, url_or_id)
        if m:
            return m.group(1)
    raise TranscriptError(f"No se pudo extraer el ID de YouTube de: {url_or_id!r}")


def fetch_transcript(
    url_or_id: str,
    languages: list[str] | None = None,
) -> TranscriptResult:
    """Obtiene la transcripción con timestamps priorizando español.

    Prefiere subtítulos manuales sobre autogenerados. Lanza TranscriptError
    (para que la capa API devuelva 422 y NestJS haga fallback a Whisper).
    """
    video_id = extract_video_id(url_or_id)
    languages = languages or settings.transcript_languages

    ytt = YouTubeTranscriptApi()
    try:
        transcript_list = ytt.list(video_id)
        # 1) manual en español  2) autogenerado en español
        try:
            transcript = transcript_list.find_manually_created_transcript(languages)
        except NoTranscriptFound:
            transcript = transcript_list.find_generated_transcript(languages)

        fetched = transcript.fetch()
    except (TranscriptsDisabled, NoTranscriptFound) as exc:
        raise TranscriptError(
            f"Sin subtitulos en espanol para {video_id}: {exc.__class__.__name__}. "
            "Usar fallback Whisper."
        ) from exc
    except VideoUnavailable as exc:
        raise TranscriptError(f"Video no disponible: {video_id}") from exc

    cues = [
        TranscriptCue(start=round(float(item["start"]), 3),
                      duration=round(float(item["duration"]), 3),
                      text=item["text"].replace("\n", " ").strip())
        for item in fetched.to_raw_data()
        if item["text"].strip()
    ]

    return TranscriptResult(
        video_id=video_id,
        language=transcript.language_code,
        source="api",
        is_generated=transcript.is_generated,
        cues=cues,
    )
