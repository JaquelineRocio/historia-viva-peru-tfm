"""El modelo configurado debe estar cargado antes de aceptar solicitudes."""
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app.main as main
from app.ml import beto


@pytest.fixture
def configured_model(monkeypatch, tmp_path):
    monkeypatch.setattr(main.settings, 'default_model_repo', 'test/model')
    monkeypatch.setattr(main.settings, 'storage_dir', str(tmp_path))
    monkeypatch.setattr(main.settings, 'default_model_path', str(tmp_path / 'model'))
    monkeypatch.setattr(main, '_model_bootstrap', {'status': 'disabled', 'error': None, 'repo': 'test/model'})
    monkeypatch.setitem(sys.modules, 'huggingface_hub', SimpleNamespace(snapshot_download=lambda **kwargs: None))


def test_bootstrap_finishes_loading_in_the_startup_thread(configured_model, monkeypatch):
    calls = []
    caller = threading.get_ident()
    monkeypatch.setattr(beto, 'load_model', lambda path: calls.append(threading.get_ident()))
    main.bootstrap_default_model()
    assert calls == [caller]
    assert main._model_bootstrap['status'] == 'ready'


def test_successful_startup_serves_ready_model(configured_model, monkeypatch):
    state = {'loaded': False}
    def load(path):
        state['loaded'] = True
    monkeypatch.setattr(beto, 'load_model', load)
    monkeypatch.setattr(beto, 'is_loaded', lambda: state['loaded'])
    with TestClient(main.app) as client:
        body = client.get('/health').json()['components']['beto']
        assert body['ready'] is True
        assert body['status'] == 'ready'


def test_import_failure_prevents_startup(configured_model, monkeypatch):
    def fail(path):
        raise ImportError('cannot import AutoModelForSequenceClassification')
    monkeypatch.setattr(beto, 'load_model', fail)
    with pytest.raises(RuntimeError, match='inicializar'):
        with TestClient(main.app):
            pytest.fail('No debe aceptar solicitudes con un modelo configurado que no cargó')
    assert main._model_bootstrap['status'] == 'error'


def test_bootstrap_without_default_model_keeps_manual_loading_available(monkeypatch):
    monkeypatch.setattr(main.settings, 'default_model_repo', None)
    def unexpected():
        pytest.fail('No debe intentar cargar un modelo sin configuración')
    monkeypatch.setattr(main, '_load_default_model', unexpected)
    with TestClient(main.app) as client:
        assert client.get('/health').status_code == 200


def test_successful_retry_clears_previous_bootstrap_error(configured_model, monkeypatch):
    monkeypatch.setattr(beto, 'load_model', lambda path: None)
    main._model_bootstrap.update(status='error', error='previous failure')
    main.bootstrap_default_model()
    assert main._model_bootstrap['status'] == 'ready'
    assert main._model_bootstrap['error'] is None
