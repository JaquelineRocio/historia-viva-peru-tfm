"""Proveedor opcional de subtitulos con timestamps mediante Supadata."""
from __future__ import annotations

import time

import httpx

from app.transcription.youtube import (
    TranscriptCue,
    TranscriptError,
    TranscriptResult,
    extract_video_id,
)


_BASE_URL = "https://api.supadata.ai/v1/transcript"


def _result(payload: dict, video_id: str) -> TranscriptResult:
    content = payload.get("content")
    if not isinstance(content, list) or not content:
        raise TranscriptError("Supadata no devolvio subtitulos con timestamps")

    cues = [
        TranscriptCue(
            start=round(float(item.get("offset", 0)) / 1000, 3),
            duration=round(float(item.get("duration", 0)) / 1000, 3),
            text=str(item.get("text", "")).replace("\n", " ").strip(),
        )
        for item in content
        if str(item.get("text", "")).strip()
    ]
    if not cues:
        raise TranscriptError("Supadata devolvio una transcripcion vacia")

    return TranscriptResult(
        video_id=video_id,
        language=str(payload.get("lang") or "es"),
        source="api",
        is_generated=False,
        cues=cues,
    )


def fetch_supadata_transcript(
    url_or_id: str,
    api_key: str,
    languages: list[str] | None = None,
) -> TranscriptResult:
    """Obtiene subtitulos nativos; no consume generacion de IA por minuto."""
    video_id = extract_video_id(url_or_id)
    url = f"https://www.youtube.com/watch?v={video_id}"
    language = (languages or ["es"])[0]
    headers = {"x-api-key": api_key}

    try:
        with httpx.Client(timeout=65) as client:
            response = client.get(
                _BASE_URL,
                params={"url": url, "lang": language, "text": "false", "mode": "native"},
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()

            job_id = payload.get("jobId") if isinstance(payload, dict) else None
            if job_id:
                for _ in range(12):
                    time.sleep(5)
                    poll = client.get(f"{_BASE_URL}/{job_id}", headers=headers)
                    poll.raise_for_status()
                    payload = poll.json()
                    status = payload.get("status")
                    if status == "completed":
                        break
                    if status == "failed":
                        raise TranscriptError("Supadata no pudo completar la transcripcion")
                else:
                    raise TranscriptError("Supadata excedio el tiempo de espera")
    except TranscriptError:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        raise TranscriptError(f"Supadata no pudo obtener la transcripcion: {exc}") from exc

    return _result(payload, video_id)
