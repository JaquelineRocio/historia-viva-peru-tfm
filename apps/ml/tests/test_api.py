"""Tests de humo de los endpoints FastAPI (sin dependencias pesadas)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.transcription.youtube import TranscriptError

client = TestClient(app)


# ----------------------------- health / segment ------------------------------
def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_segment_ok():
    cues = [{"start": 0.0, "duration": 30.0, "text": "hola"}, {"start": 30.0, "duration": 30.0, "text": "mundo"}]
    r = client.post("/segment", json={"cues": cues, "window_sec": 60, "overlap_sec": 10})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == len(body["segments"]) > 0


def test_segment_malformed_cue_returns_400():
    r = client.post("/segment", json={"cues": [{"texto": "sin start"}]})
    assert r.status_code == 400


def test_segment_invalid_overlap_returns_400():
    cues = [{"start": 0.0, "duration": 30.0, "text": "hola"}]
    r = client.post("/segment", json={"cues": cues, "window_sec": 60, "overlap_sec": 60})
    assert r.status_code == 400


# ----------------------------- transcribe ------------------------------------
def test_transcribe_ok(monkeypatch):
    class FakeResult:
        def to_dict(self):
            return {"video_id": "abc", "cues": [], "full_text": ""}

    monkeypatch.setattr("app.main.fetch_transcript", lambda url, langs: FakeResult())
    r = client.post("/transcribe", json={"youtube_url": "https://youtu.be/abc"})
    assert r.status_code == 200
    assert r.json()["video_id"] == "abc"


def test_transcribe_without_subtitles_returns_422(monkeypatch):
    def boom(url, langs):
        raise TranscriptError("Sin subtitulos")

    monkeypatch.setattr("app.main.fetch_transcript", boom)
    r = client.post("/transcribe", json={"youtube_url": "https://youtu.be/abc"})
    assert r.status_code == 422


# ----------------------------- jobs / infer / models -------------------------
def test_unknown_job_returns_404():
    r = client.get("/jobs/no-existe")
    assert r.status_code == 404


def test_infer_without_model_returns_409():
    r = client.post("/infer", json={"texts": ["hola"]})
    assert r.status_code == 409


def test_models_load_path_traversal_returns_400():
    r = client.post("/models/load", json={"artifact_path": "../../etc/passwd"})
    assert r.status_code == 400


def test_train_path_traversal_returns_400():
    payload = {
        "version_tag": "v1",
        "labels": ["a", "b"],
        "items": [],
        "base_model": "x",
        "output_dir": "../fuera",
    }
    r = client.post("/train", json=payload)
    assert r.status_code == 400


# ----------------------------- auth interna ----------------------------------
@pytest.fixture
def with_token(monkeypatch):
    monkeypatch.setattr(settings, "internal_token", "secreto")


def test_token_required_when_configured(with_token):
    r = client.post("/segment", json={"cues": []})
    assert r.status_code == 401


def test_token_accepted_when_valid(with_token):
    r = client.post("/segment", json={"cues": []}, headers={"X-Internal-Token": "secreto"})
    assert r.status_code == 200


def test_health_exempt_from_token(with_token):
    assert client.get("/health").status_code == 200
