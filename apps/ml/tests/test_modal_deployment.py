import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
from verify_modal_deployment import verify

SHA = 'a' * 40


def run(*, health_sha=SHA, infer_sha=SHA, ready=True, prediction=None):
    def respond(request):
        if request.url.path == '/health':
            return httpx.Response(200, json={'status': 'ok', 'deployment_sha': health_sha,
                'components': {'beto': {'ready': ready, 'status': 'ready' if ready else 'loading'}}})
        return httpx.Response(200, json={'deployment_sha': infer_sha,
            'predictions': [prediction if prediction is not None else {'label': 'no_relevante', 'confidence': .8}]})
    with httpx.Client(base_url='https://example.test', transport=httpx.MockTransport(respond)) as client:
        return verify(client, SHA, attempts=1)


def test_matching_commit_and_prediction_pass():
    assert run()['passed'] is True


@pytest.mark.parametrize('options,reason', [
    ({'health_sha': 'b' * 40}, 'health_sha_mismatch'),
    ({'infer_sha': 'b' * 40}, 'inference_sha_mismatch'),
    ({'ready': False}, 'beto_not_ready'),
    ({'prediction': {'label': '', 'confidence': .8}}, 'invalid_prediction'),
    ({'prediction': {'label': 'no_relevante', 'confidence': 1.1}}, 'invalid_prediction'),
])
def test_wrong_version_or_unusable_model_fails(options, reason):
    report = run(**options)
    assert report['passed'] is False
    assert report['attempts'][0]['reason'] == reason


def test_retries_temporary_unavailability():
    calls = []
    def respond(request):
        calls.append(request.url.path)
        if len(calls) == 1:
            return httpx.Response(503)
        if request.url.path == '/health':
            return httpx.Response(200, json={'status': 'ok', 'deployment_sha': SHA,
                'components': {'beto': {'ready': True, 'status': 'ready'}}})
        return httpx.Response(200, json={'deployment_sha': SHA, 'predictions': [{'label': 'no_relevante', 'confidence': .5}]})
    with httpx.Client(base_url='https://example.test', transport=httpx.MockTransport(respond)) as client:
        report = verify(client, SHA, attempts=2, retry_delay=0)
    assert report['passed'] is True and len(report['attempts']) == 2


def test_auth_failure_stops_without_logging_response_or_credentials():
    with httpx.Client(base_url='https://example.test', headers={'Modal-Secret': 'private-token'},
                     transport=httpx.MockTransport(lambda req: httpx.Response(401, text='private-error-body'))) as client:
        report = verify(client, SHA, attempts=3, retry_delay=0)
    assert report['passed'] is False and len(report['attempts']) == 1
    assert 'private-' not in json.dumps(report)


def test_service_reports_deployment_sha(monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from fastapi.testclient import TestClient
    from app.main import app
    from app.config import settings
    from app.ml import beto
    monkeypatch.setattr(settings, 'deployment_sha', SHA)
    monkeypatch.setattr(settings, 'internal_token', None)
    monkeypatch.setattr(beto, 'is_loaded', lambda: True)
    monkeypatch.setattr(beto, 'infer', lambda texts: [{'label': 'no_relevante', 'confidence': .5}])
    client = TestClient(app)
    assert client.get('/health').json()['deployment_sha'] == SHA
    assert client.post('/infer', json={'texts': ['ejemplo']}).json()['deployment_sha'] == SHA
