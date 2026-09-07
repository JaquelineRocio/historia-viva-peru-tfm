"""Comprobaciones funcionales con informe; credenciales solo por entorno."""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx


def run_checks(client, *, username: str, password: str, web_url: str | None = None) -> list[dict]:
    checks = []

    def check(name, operation):
        start = time.monotonic()
        try:
            operation()
            checks.append({"name": name, "status": "passed", "seconds": round(time.monotonic() - start, 2)})
        except Exception as exc:
            # No escribir cuerpos HTTP, tokens ni URLs con credenciales en el informe.
            checks.append({"name": name, "status": "failed", "error_type": type(exc).__name__,
                           "seconds": round(time.monotonic() - start, 2)})
        return checks[-1]["status"] == "passed"

    def health():
        response = client.get("/api/health")
        response.raise_for_status()
        body = response.json()
        assert body.get("status") == "ok" and body.get("ml") == "ok", "API o ML no saludable"

    check("API and ML health", health)

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
