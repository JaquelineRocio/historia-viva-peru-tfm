"""Comprueba la importación local y en un worker sin checkout, sin desplegar."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import modal

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(name, None)


def check() -> dict:
    source = ROOT / "apps/ml/modal_app.py"
    with patch.object(modal, "is_local", return_value=True):
        local = load(source, "modal_local_import_check")
    if local.image is None or not local.RELEASE["revision"]:
        raise RuntimeError("El cliente no preparó la imagen y la revisión")
    before = sys.path[:]
    try:
        with tempfile.TemporaryDirectory(prefix="modal-worker-") as directory:
            relocated = Path(directory) / "modal_app.py"
            shutil.copyfile(source, relocated)
            # Ningún archivo del checkout se monta aquí. El manifiesto y los
            # requirements solo deben leerse al construir la imagen en el cliente.
            with patch.object(modal, "is_local", return_value=False), patch.object(
                Path, "read_text", side_effect=AssertionError("El worker intentó leer archivos locales")
            ):
                remote = load(relocated, "modal_remote_import_check")
            if remote.image is not None or "RELEASE" in vars(remote):
                raise RuntimeError("El worker volvió a construir la imagen")
            if not isinstance(remote.ml_api, modal.Function):
                raise RuntimeError("No se registró la función remota")
    finally:
        sys.path[:] = before
    return {"passed": True, "modal_version": modal.__version__, "local_import": True,
            "worker_import_without_checkout": True, "remote_deployment_executed": False}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
