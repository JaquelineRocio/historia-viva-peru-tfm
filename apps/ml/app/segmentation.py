"""Segmentación de transcripciones en ventanas temporales con solape.

Estrategia v1 (robusta y determinista): agrupa los cues de subtítulos en
ventanas de `window_sec` segundos con `overlap_sec` de solape para no cortar
ideas a la mitad. La segmentación semántica (embeddings) queda como mejora v2.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class Segment:
    idx: int
    start_sec: float
    end_sec: float
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def segment_by_time(
    cues: list[dict],
    window_sec: float = 60.0,
    overlap_sec: float = 10.0,
) -> list[Segment]:
    """Agrupa cues [{start, duration|end, text}] en ventanas temporales.

    Cada cue se asigna a la ventana cuyo rango [win_start, win_start+window)
    contiene su `start`. El solape se logra avanzando el paso en
    (window_sec - overlap_sec).
    """
    if window_sec <= 0:
        raise ValueError("window_sec debe ser > 0")
    if overlap_sec < 0 or overlap_sec >= window_sec:
        raise ValueError("overlap_sec debe estar en [0, window_sec)")
    if not cues:
        return []
    for c in cues:
        if not isinstance(c.get("start"), (int, float)) or not isinstance(c.get("text"), str):
            raise ValueError("Cada cue debe tener 'start' numérico y 'text' string")

    step = window_sec - overlap_sec
    total_end = max(float(c.get("end", c["start"] + c.get("duration", 0.0))) for c in cues)

    segments: list[Segment] = []
    idx = 0
    win_start = 0.0
    while win_start < total_end:
        win_end = win_start + window_sec
        chunk = [
            c for c in cues
            if win_start <= float(c["start"]) < win_end
        ]
        if chunk:
            text = " ".join(c["text"].strip() for c in chunk if c["text"].strip())
            if text:
                real_start = min(float(c["start"]) for c in chunk)
                real_end = max(
                    float(c.get("end", c["start"] + c.get("duration", 0.0))) for c in chunk
                )
                segments.append(Segment(
                    idx=idx,
                    start_sec=round(real_start, 3),
                    end_sec=round(real_end, 3),
                    text=text,
                ))
                idx += 1
        win_start += step

    return segments
