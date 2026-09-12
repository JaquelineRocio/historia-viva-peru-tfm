"""Contratos de publicación, rechazo de corrupción y selección tras verificación."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps/ml"))
sys.path.insert(0, str(ROOT / "scripts"))
from app.ml.model_release import MODEL_FILES, download_release, read_release, validate_release, verify_files
from publish_model import prepare, publish, write_json


@pytest.fixture
def prepared(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    labels = [f"class_{i}" for i in range(7)]
    for name in MODEL_FILES:
        (source / name).write_bytes(b"synthetic fixture")
    write_json(source / "config.json", {"id2label": {str(i): s for i, s in enumerate(labels)}})
    write_json(source / "labels.json", {"labels": labels, "max_length": 384})
    card = tmp_path / "card.md"
    card.write_text("Experimental fixture", encoding="utf-8")
    (source / "private-corpus.json").write_text("must not upload", encoding="utf-8")
    package, release, hashes = prepare(source, tmp_path / "delivery", "owner/model", card)
    return source, package, release, hashes


def test_prepare_preserves_weights_and_excludes_corpus(prepared):
    source, package, release, hashes = prepared
    assert set(p.name for p in package.iterdir()) == {*MODEL_FILES, "README.md"}
    assert release["files"]["model.safetensors"] == hashes["model.safetensors"]
    assert "labels" in json.loads((source / "labels.json").read_text())
    assert json.loads((package / "labels.json").read_text())["max_len"] == 384
    verify_files(package, release)


def test_rejects_changed_weights(prepared):
    _, package, release, _ = prepared
    (package / "model.safetensors").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="Hash incorrecto"):
        verify_files(package, release)


def test_rejects_wrong_label_order_even_with_valid_hashes(prepared):
    _, package, release, _ = prepared
    release["labels"].reverse()
    with pytest.raises(ValueError, match="orden"):
        verify_files(package, release)


@pytest.mark.parametrize("change", [
    {"revision": "main"}, {"revision": "abc123"}, {"max_len": True},
    {"files": {"../escape": "a" * 64}}, {"labels": ["same"] * 7},
])
def test_invalid_release_fails(prepared, change):
    release = {**prepared[2], "revision": "a" * 40, **change}
    with pytest.raises(ValueError):
        validate_release(release)


def test_source_label_mismatch_cannot_be_packaged(prepared, tmp_path):
    source, package, _, _ = prepared
    write_json(source / "labels.json", {"labels": ["wrong"] * 7, "max_length": 384})
    with pytest.raises(ValueError, match="orden"):
        prepare(source, tmp_path / "other", "owner/model", package / "README.md")


class FakeHub:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def create_repo(self, **kwargs):
        self.calls.append(("create", kwargs))

    def model_info(self, repo):
        return SimpleNamespace(private=False, gated=False, sha="b" * 40)

    def upload_folder(self, **kwargs):
        self.calls.append(("upload", kwargs))
        if self.fail:
            raise RuntimeError("network failure")
        return SimpleNamespace(oid="a" * 40)


def test_publish_selects_only_verified_remote_revision_and_saves_rollback(prepared, tmp_path):
    _, package, release, _ = prepared
    manifest = tmp_path / "configs/production-model.json"
    previous = {**release, "revision": "b" * 40}
    write_json(manifest, previous)
    hub, requests = FakeHub(), []
    def download(**kwargs):
        requests.append(kwargs)
        assert manifest.read_text(encoding="utf-8") == json.dumps(previous, ensure_ascii=False, indent=2) + "\n"
        return package / kwargs["filename"]
    result = publish(package, release, manifest, api=hub, download=download)
    assert read_release(manifest) == result
    assert result["revision"] == "a" * 40
    assert all(r["revision"] == "a" * 40 and r["token"] is False for r in requests)
    assert len(requests) == 7
    upload = hub.calls[1][1]
    assert upload["parent_commit"] == "b" * 40
    assert set(upload["allow_patterns"]) == {*MODEL_FILES, "README.md"}
    assert read_release(manifest.parent / "model-releases" / ("b" * 40 + ".json")) == previous


@pytest.mark.parametrize("fail_upload", [False, True])
def test_remote_failure_preserves_selection(prepared, tmp_path, fail_upload):
    _, package, release, _ = prepared
    manifest = tmp_path / "production-model.json"
    write_json(manifest, {**release, "revision": "b" * 40})
    before = manifest.read_bytes()
    bad = tmp_path / "wrong"
    bad.write_bytes(b"different remote bytes")
    with pytest.raises((ValueError, RuntimeError)):
        publish(package, release, manifest, api=FakeHub(fail=fail_upload), download=lambda **kw: bad)
    assert manifest.read_bytes() == before


def test_download_pins_revision_and_checks_content(prepared, monkeypatch):
    _, package, release, _ = prepared
    release = {**release, "revision": "a" * 40}
    calls = []
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(snapshot_download=lambda **kw: calls.append(kw)))
    download_release(release, package)
    assert calls[0]["revision"] == "a" * 40
    assert set(calls[0]["allow_patterns"]) == set(MODEL_FILES)
    (package / "tokenizer.json").write_bytes(b"wrong")
    with pytest.raises(ValueError, match="Hash incorrecto"):
        download_release(release, package)


def test_committed_production_manifest_is_valid_and_has_rollback():
    release = read_release(ROOT / "configs/production-model.json")
    assert read_release(ROOT / "configs/model-releases" / (release["revision"] + ".json")) == release


def test_pinned_startup_uses_verified_local_files_and_bound_identity(prepared, monkeypatch):
    import app.main as main
    from app.ml import beto
    _, package, release, _ = prepared
    release = {**release, "revision": "a" * 40}
    monkeypatch.setattr(main.settings, "storage_dir", str(package.parent))
    monkeypatch.setattr(main.settings, "default_model_path", str(package))
    monkeypatch.setattr(main.settings, "default_model_release", json.dumps(release))
    monkeypatch.setattr(main, "_model_bootstrap", {"status": "disabled"})
    def no_network(**kwargs):
        pytest.fail("Verified image must start offline")
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(snapshot_download=no_network))
    calls = []
    monkeypatch.setattr(beto, "load_model", lambda path, **kw: calls.append((path, kw)))
    main.bootstrap_default_model()
    assert calls == [(str(package), {"release": release})]
    assert main._model_bootstrap["status"] == "ready"


def test_modal_recipe_pins_download_and_rejects_bad_build_files(prepared, monkeypatch):
    import runpy
    import shlex
    import shutil
    import subprocess
    from app.ml import model_release
    _, package, release, _ = prepared
    release = {**release, "revision": "a" * 40}
    monkeypatch.setattr(model_release, "read_release", lambda path: release)
    captured = {}
    class FakeImage:
        @classmethod
        def debian_slim(cls, **kwargs):
            return cls()
        def pip_install(self, *args, **kwargs):
            return self
        def pip_install_from_requirements(self, *args):
            return self
        def apt_install(self, *args):
            return self
        def run_commands(self, code):
            captured["command"] = code
            return self
        def env(self, value):
            captured["env"] = value
            return self
        def add_local_dir(self, *args):
            return self
    decorator = lambda **kw: lambda fn: fn
    fake = SimpleNamespace(Image=FakeImage,
        App=lambda name: SimpleNamespace(function=decorator),
        Secret=SimpleNamespace(from_name=lambda name: name), concurrent=decorator, asgi_app=decorator)
    monkeypatch.setitem(sys.modules, "modal", fake)
    namespace = runpy.run_path(str(ROOT / "apps/ml/modal_app.py"))
    assert json.loads(captured["env"]["ML_DEFAULT_MODEL_RELEASE"]) == release
    # Modal convierte cada línea física en una instrucción RUN independiente.
    # Una cadena multilínea pasa shlex.split pero se rompe en el builder real.
    assert len(captured["command"].splitlines()) == 1
    shell = shutil.which("sh")
    if shell is None and Path("C:/Program Files/Git/usr/bin/sh.exe").is_file():
        shell = "C:/Program Files/Git/usr/bin/sh.exe"
    if shell:
        # Comprobar cada RUN como lo recibe el shell, sin ejecutar descargas.
        for line in captured["command"].splitlines():
            syntax = subprocess.run([shell, "-n", "-c", line], capture_output=True, text=True)
            assert syntax.returncode == 0, syntax.stderr
    parts = shlex.split(captured["command"])
    assert parts[:2] == ["python", "-c"]
    assert parts[2] == namespace["BUILD_CODE"]
    code = parts[2].replace(repr(namespace["REMOTE_MODEL"]), repr(str(package)))
    calls = []
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(snapshot_download=lambda **kw: calls.append(kw)))
    exec(compile(code, "modal-build", "exec"), {})
    assert calls[0]["revision"] == release["revision"]
    assert set(calls[0]["allow_patterns"]) == set(MODEL_FILES)
    (package / "model.safetensors").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="hash mismatch"):
        exec(compile(code, "modal-build", "exec"), {})


def test_loaded_identity_is_cleared_on_manual_replacement(prepared, monkeypatch):
    from app.ml import beto
    from app.ml.model_release import identity
    _, package, release, _ = prepared
    release = {**release, "revision": "a" * 40}
    model = SimpleNamespace(eval=lambda: None)
    factory = SimpleNamespace(from_pretrained=lambda *args, **kw: model)
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(
        AutoModelForSequenceClassification=factory, AutoTokenizer=factory))
    monkeypatch.setattr(beto, "_active", None)
    beto.load_model(str(package), release=release)
    assert beto.model_identity() == identity(release)
    beto.load_model(str(package))
    assert beto.model_identity() == {}


def save_receipt(prepared):
    _, package, release, hashes = prepared
    path = package.parent / f"{package.name}-verification.json"
    write_json(path, {"release": release, "source_files": hashes,
        "verification": {"passed": True, "tokenization_equal": True, "texts": 5,
                         "predictions": [{"label": release["labels"][0], "confidence": .5}] * 5}})
    return path


def test_reuse_checks_saved_files_without_loading_model(prepared):
    from publish_model import reuse_package
    save_receipt(prepared)
    _, package, release, _ = prepared
    assert reuse_package(package) == (package, release)
    (package / "model.safetensors").write_bytes(b"changed")
    with pytest.raises(ValueError, match="Hash incorrecto"):
        reuse_package(package)


@pytest.mark.parametrize("defect", ["missing", "failed", "incomplete", "wrong_source"])
def test_reuse_rejects_invalid_receipts(prepared, defect):
    from publish_model import PublicationError, reuse_package
    receipt = save_receipt(prepared)
    data = json.loads(receipt.read_text(encoding="utf-8"))
    if defect == "missing":
        receipt.unlink()
    else:
        if defect == "failed":
            data["verification"]["passed"] = False
        elif defect == "incomplete":
            data["verification"]["predictions"] = []
        else:
            data["source_files"]["model.safetensors"] = "b" * 64
        write_json(receipt, data)
    with pytest.raises(PublicationError):
        reuse_package(prepared[1])


@pytest.mark.parametrize("role", ["read", "write", "fineGrained"])
def test_auth_rejects_read_only_tokens(role):
    from publish_model import PublicationError, check_auth
    api = SimpleNamespace(whoami=lambda: {"auth": {"accessToken": {"role": role}}})
    if role == "read":
        with pytest.raises(PublicationError, match="solo permite lectura"):
            check_auth(api)
    else:
        check_auth(api)


@pytest.mark.parametrize("status", [401, 403, 503])
def test_auth_error_does_not_expose_server_body(status):
    from publish_model import PublicationError, check_auth
    error = RuntimeError("secret-response-body")
    error.response = SimpleNamespace(status_code=status)
    def whoami():
        raise error
    with pytest.raises(PublicationError) as caught:
        check_auth(SimpleNamespace(whoami=whoami))
    assert "secret-response-body" not in str(caught.value)


def test_missing_auth_stops_before_packaging_or_inference(monkeypatch, capsys):
    import publish_model as command
    monkeypatch.setattr(sys, "argv", ["publish_model.py", "publish"])
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(get_token=lambda: None, HfApi=lambda: None))
    monkeypatch.setattr(command, "prepare", lambda *a: pytest.fail("Must check auth first"))
    monkeypatch.setattr(command, "smoke", lambda *a: pytest.fail("Must not infer"))
    assert command.cli() == 1
    assert "auth login" in capsys.readouterr().err


def test_cli_resume_uses_receipt_without_new_inference(prepared, monkeypatch, tmp_path):
    import publish_model as command
    save_receipt(prepared)
    package, release = prepared[1:3]
    monkeypatch.setattr(sys, "argv", ["publish_model.py", "publish", "--package", str(package)])
    monkeypatch.setattr(command, "authenticated_api", lambda: "authenticated")
    monkeypatch.setattr(command, "prepare", lambda *a: pytest.fail("Must reuse"))
    monkeypatch.setattr(command, "smoke", lambda *a: pytest.fail("Must not repeat inference"))
    calls = []
    def upload(p, r, m, **kw):
        calls.append((p, r, kw))
        return {**r, "revision": "a" * 40}
    monkeypatch.setattr(command, "publish", upload)
    assert command.cli() == 0
    assert calls == [(package, release, {"api": "authenticated"})]


def test_write_auth_failure_has_actionable_message_without_traceback(monkeypatch, capsys):
    import publish_model as command
    error = RuntimeError("secret-response-body")
    error.response = SimpleNamespace(status_code=403)
    def failure():
        raise error
    monkeypatch.setattr(command, "main", failure)
    assert command.cli() == 1
    message = capsys.readouterr().err
    assert "403" in message and "auth login" in message
    assert "secret-response-body" not in message
