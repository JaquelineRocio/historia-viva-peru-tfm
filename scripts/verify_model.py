"""Pruebas funcionales locales contra FastAPI con pesos BETO reales.

Ejecuta la aplicación en proceso, sin conectarse a producción ni modificar su BD.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/ml"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    import torch
    from fastapi.testclient import TestClient
    from app.config import settings
    from app.main import app

    torch.set_num_threads(4)
    model = Path(args.model).resolve()
    settings.storage_dir = str(model.parent)
    settings.internal_token = "local-functional-check"
    headers = {"X-Internal-Token": settings.internal_token}
    client = TestClient(app)
    texts = ["San Martín organizó la expedición libertadora del Perú.",
             "La Constitución estableció la organización política de la nueva república."]
    cases = []
    try:
        blocked = client.post("/infer", json={"texts": texts})
        assert blocked.status_code == 401
        cases.append({"id": "ML-01", "name": "Unauthorized prediction rejected", "passed": True})
        loaded = client.post("/models/load", json={"artifact_path": str(model)}, headers=headers)
        assert loaded.status_code == 200 and loaded.json()["loaded"] is True
        labels = loaded.json()["labels"]
        before = client.post("/infer", json={"texts": texts}, headers=headers)
        assert before.status_code == 200
        predictions = before.json()["predictions"]
        assert len(predictions) == len(texts)
        assert all(p["label"] in labels and 0 <= p["confidence"] <= 1 for p in predictions)
        cases.append({"id": "ML-02", "name": "Load real BETO and predict through API", "passed": True,
                      "inputs": texts, "predictions": predictions,
                      "scope": "Contract and inference execution; not a semantic accuracy test"})
        missing = model.parent / "missing-functional-check-model"
        assert not missing.exists()
        failure = client.post("/models/load", json={"artifact_path": str(missing)}, headers=headers)
        assert failure.status_code == 404
        after = client.post("/infer", json={"texts": texts}, headers=headers)
        assert after.status_code == 200 and after.json() == before.json()
        cases.append({"id": "ML-03", "name": "Failed replacement preserves active predictions", "passed": True})
    except Exception as exc:
        cases.append({"id": "failure", "passed": False, "error_type": type(exc).__name__})
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "environment": "local-in-process-fastapi",
              "model": model.name, "cases": cases, "passed": len(cases) == 3 and all(c["passed"] for c in cases)}
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
