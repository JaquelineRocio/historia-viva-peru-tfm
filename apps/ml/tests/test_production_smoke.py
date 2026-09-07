import json
import sys
from pathlib import Path

import httpx
import pytest

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


def test_smoke_requires_ml_health_not_only_http_200(monkeypatch):
    sleeps = []
    monkeypatch.setattr("smoke_deployment.time.sleep", sleeps.append)
    with httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(lambda r: responses(r, ml="unreachable"))) as client:
        checks = run_checks(client, username="demo", password="correct")
    assert checks[0]["status"] == "failed"
    assert len(checks[0]["attempts"]) == 4
    assert sleeps == [10, 10, 10]
    assert checks[0]["recovered_after_retry"] is False
    assert "example-token" not in json.dumps(checks)


def test_smoke_rejects_false_abstention_with_evidence():
    with httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(lambda r: responses(r, evidence=[{"id": 1}]))) as client:
        checks = run_checks(client, username="demo", password="correct")
    assert checks[-1]["status"] == "failed"
    assert len(checks[-1]["attempts"]) == 1


def test_smoke_happy_path():
    with httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(responses)) as client:
        checks = run_checks(client, username="demo", password="correct")
    assert len(checks) == 5
    assert all(c["status"] == "passed" for c in checks)
    assert all(len(c["attempts"]) == 1 for c in checks)


@pytest.mark.parametrize("initial_failure", ["unreachable", "timeout", "http503"])
def test_health_recovers_and_preserves_failed_attempt(initial_failure, monkeypatch):
    sleeps = []
    monkeypatch.setattr("smoke_deployment.time.sleep", sleeps.append)
    health_calls = 0

    def handler(request):
        nonlocal health_calls
        if request.url.path == "/api/health":
            health_calls += 1
            if health_calls == 1:
                if initial_failure == "timeout":
                    raise httpx.ReadTimeout("private-detail-do-not-log", request=request)
                if initial_failure == "http503":
                    return httpx.Response(503, text="private-detail-do-not-log")
                return responses(request, ml="unreachable")
        return responses(request)

    with httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler)) as client:
        checks = run_checks(client, username="demo", password="correct")
    assert all(c["status"] == "passed" for c in checks)
    assert checks[0]["recovered_after_retry"] is True
    assert [a["status"] for a in checks[0]["attempts"]] == ["failed", "passed"]
    assert sleeps == [10]
    assert "private-detail" not in json.dumps(checks)


def test_health_auth_failure_is_not_retried(monkeypatch):
    sleeps = []
    monkeypatch.setattr("smoke_deployment.time.sleep", sleeps.append)

    def handler(request):
        if request.url.path == "/api/health":
            return httpx.Response(401)
        return responses(request)

    with httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler)) as client:
        checks = run_checks(client, username="demo", password="correct")
    assert checks[0]["status"] == "failed"
    assert checks[0]["attempts"][0]["http_status"] == 401
    assert len(checks[0]["attempts"]) == 1
    assert sleeps == []
