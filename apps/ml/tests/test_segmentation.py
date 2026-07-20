"""Tests de la segmentación por ventanas temporales."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.segmentation import segment_by_time


def _cues():
    # 5 cues de ~30s cada uno → 0..150s
    return [
        {"start": 0.0, "duration": 30.0, "text": "uno"},
        {"start": 30.0, "duration": 30.0, "text": "dos"},
        {"start": 60.0, "duration": 30.0, "text": "tres"},
        {"start": 90.0, "duration": 30.0, "text": "cuatro"},
        {"start": 120.0, "duration": 30.0, "text": "cinco"},
    ]


def test_empty_cues_returns_empty():
    assert segment_by_time([]) == []


def test_windows_have_overlap_and_indices():
    segs = segment_by_time(_cues(), window_sec=60, overlap_sec=10)
    assert len(segs) > 0
    # índices consecutivos desde 0
    assert [s.idx for s in segs] == list(range(len(segs)))
    # primer segmento arranca en 0
    assert segs[0].start_sec == 0.0
    # el texto no queda vacío
    assert all(s.text for s in segs)


def test_invalid_overlap_raises():
    import pytest

    with pytest.raises(ValueError):
        segment_by_time(_cues(), window_sec=60, overlap_sec=60)
    with pytest.raises(ValueError):
        segment_by_time(_cues(), window_sec=0, overlap_sec=0)


def test_window_covers_full_duration():
    segs = segment_by_time(_cues(), window_sec=60, overlap_sec=10)
    # el último segmento debe alcanzar cerca del final (150s)
    assert segs[-1].end_sec >= 120.0
