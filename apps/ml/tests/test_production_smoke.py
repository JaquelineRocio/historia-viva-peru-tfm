import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from smoke_deployment import run_checks


def responses(request, *, ml="ok", evidence=None):
    if request.url.path == "/api/health":
        return httpx.Response(200, json={"status": "ok", "ml": ml})
    if request.url.path == "/api/auth/login":
        data = json.loads(request.content)
        if data["password"] != "correct":
            return httpx.Response(401)
        return httpx.Response(200, json={"accessToken": "example-token-do-not-log"})
    if request.url.path == "/api/projects":
        return httpx.Response(200, json=[{"id": "project"}])
    return httpx.Response(200, json={"mode": "abstained", "evidence": evidence or [],
                                   "answer": "No encuentro respaldo suficiente en las fuentes disponibles."})


def test_smoke_requires_ml_health_not_only_http_200():
    with httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(lambda r: responses(r, ml="unreachable"))) as client:
        checks = run_checks(client, username="demo", password="correct")
    assert checks[0]["status"] == "failed"
    assert "example-token" not in json.dumps(checks)


def test_smoke_rejects_false_abstention_with_evidence():
    with httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(lambda r: responses(r, evidence=[{"id": 1}]))) as client:
        checks = run_checks(client, username="demo", password="correct")
    assert checks[-1]["status"] == "failed"


def test_smoke_happy_path():
    with httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(responses)) as client:
        checks = run_checks(client, username="demo", password="correct")
    assert len(checks) == 5
    assert all(c["status"] == "passed" for c in checks)
