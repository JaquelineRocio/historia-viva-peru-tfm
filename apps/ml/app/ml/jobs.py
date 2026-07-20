"""Registro en memoria de jobs de entrenamiento.

NestJS es el dueño del estado persistente (tabla training_jobs); este registro es
efímero y solo sirve para que NestJS haga polling de /jobs/{id} mientras el
entrenamiento corre en un BackgroundTask.
"""
from __future__ import annotations

import threading
from typing import Dict, Optional

_lock = threading.Lock()
_jobs: Dict[str, dict] = {}


def create_job(job_id: str) -> dict:
    with _lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "current_epoch": None,
            "error": None,
            "artifact_path": None,
            "metrics": None,
        }
        return dict(_jobs[job_id])


def update_job(job_id: str, **fields) -> None:
    with _lock:
        if job_id in _jobs:
            _jobs[job_id].update(fields)


def get_job(job_id: str) -> Optional[dict]:
    with _lock:
        j = _jobs.get(job_id)
        return dict(j) if j else None
