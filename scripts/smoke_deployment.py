"""Comprobaciones funcionales con informe; credenciales solo por entorno."""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx


class HealthNotReady(Exception):
    """La API respondió, pero API/ML aún no están disponibles."""


def run_checks(client, *, username: str, password: str, web_url: str | None = None,
               health_attempts: int = 4, retry_delay: float = 10) -> list[dict]:
    if health_attempts < 1 or retry_delay < 0:
        raise ValueError("Invalid health retry configuration")
    checks = []

    def check(name, operation, *, max_attempts=1):
        start = time.monotonic()
        attempts = []
        for number in range(1, max_attempts + 1):
            attempt_start = time.monotonic()
            retryable = False
            attempt = {"number": number, "status": "passed"}
            try:
                operation()
            except Exception as exc:
                # No escribir cuerpos HTTP, tokens ni URLs con credenciales.
                attempt.update(status="failed", error_type=type(exc).__name__)
                retryable = isinstance(exc, (HealthNotReady, httpx.TimeoutException, httpx.NetworkError))
                if isinstance(exc, httpx.HTTPStatusError):
                    attempt["http_status"] = exc.response.status_code
                    retryable = exc.response.status_code in (408, 429, 500, 502, 503, 504)
            attempt["seconds"] = round(time.monotonic() - attempt_start, 2)
            attempts.append(attempt)
            if attempt["status"] == "passed" or not retryable or number == max_attempts:
                break
            time.sleep(retry_delay)
        result = {"name": name, "status": attempt["status"],
                  "seconds": round(time.monotonic() - start, 2), "attempts": attempts,
                  "recovered_after_retry": len(attempts) > 1 and attempt["status"] == "passed"}
        if "error_type" in attempt:
            result["error_type"] = attempt["error_type"]
        checks.append(result)
        return result["status"] == "passed"

    def health():
        response = client.get("/api/health")
        response.raise_for_status()
        body = response.json()
        if body.get("status") != "ok" or body.get("ml") != "ok":
            raise HealthNotReady()

    check("API and ML health", health, max_attempts=health_attempts)

    def invalid_login():
        response = client.post("/api/auth/login", json={"username": username, "password": "invalid-smoke-password"})
        assert response.status_code == 401, "Se esperaba 401"

    check("Invalid credentials rejected", invalid_login)
    auth = {}

    def login():
        response = client.post("/api/auth/login", json={"username": username, "password": password})
        response.raise_for_status()
        token = response.json().get("accessToken")
        assert isinstance(token, str) and token
        auth["Authorization"] = f"Bearer {token}"

    if check("Demo login", login):
        projects = []

        def project_access():
            response = client.get("/api/projects", headers=auth)
            response.raise_for_status()
            projects.extend(response.json())
            assert projects and projects[0].get("id")

        if check("Project access", project_access):
            def abstention():
                response = client.post(f"/api/projects/{projects[0]['id']}/assistant/query", headers=auth,
                                       json={"query": "¿Qué relación tuvo Apolo 11 con la Independencia peruana?"})
                response.raise_for_status()
                body = response.json()
                assert body.get("mode") == "abstained" and body.get("evidence") == []
                assert body.get("answer") == "No encuentro respaldo suficiente en las fuentes disponibles."

            check("Out-of-scope query abstains without evidence", abstention)
    if web_url:
        def web():
            response = client.get(web_url)
            response.raise_for_status()
            assert 'id="root"' in response.text
        check("Web application shell", web)
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--web-url")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with httpx.Client(base_url=args.api_url.rstrip("/"), timeout=60, follow_redirects=True) as client:
        checks = run_checks(client, username=os.getenv("SMOKE_USERNAME", "docente"),
                            password=os.getenv("SMOKE_PASSWORD", "tfm2026"), web_url=args.web_url)
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "checks": checks,
              "passed": all(c["status"] == "passed" for c in checks)}
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
