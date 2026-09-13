"""Despliegue serverless del servicio ML en Modal.

Uso desde la raíz del repositorio:
    modal deploy apps/ml/modal_app.py

El secreto `historia-viva-ml` debe contener ML_INTERNAL_TOKEN. El modelo BETO
público se incorpora a la imagen durante el build para reducir el arranque en frío.
"""
import json
import os
import shlex
import sys
from pathlib import Path

import modal


APP_NAME = "historia-viva-peru-ml"
REMOTE_ROOT = "/opt/historia-viva-ml"
# Los workers vuelven a importar este módulo desde /root/modal_app.py.
# Solo el cliente de deploy tiene el checkout; el worker recibe la imagen ya creada.
image = None
if modal.is_local():
    ML_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(ML_DIR))
    from app.ml.model_release import read_release

    RELEASE = read_release(ML_DIR.parents[1] / "configs/production-model.json")
    MODEL_REPO = RELEASE["repo_id"]
    REMOTE_MODEL = f"/opt/models/{RELEASE['revision']}"
    # shlex.quote protege los datos; Modal divide comandos por saltos de línea,
    # incluso dentro de comillas. Mantener también el código Python en una sola línea.
    BUILD_CODE = (
        "import hashlib,json; from pathlib import Path; "
        "from huggingface_hub import snapshot_download; "
        f"r=json.loads({json.dumps(RELEASE)!r}); p=Path({REMOTE_MODEL!r}); "
        "snapshot_download(repo_id=r['repo_id'],revision=r['revision'],local_dir=str(p),"
        "allow_patterns=list(r['files']),token=False); "
        "bad=[n for n,h in r['files'].items() if hashlib.sha256((p/n).read_bytes()).hexdigest()!=h]; "
        "exec(\"if bad: raise ValueError('Model hash mismatch: '+str(bad))\")"
    )


    image = (
        modal.Image.debian_slim(python_version="3.11")
        .apt_install("ffmpeg")
        .pip_install(
            "torch==2.12.0",
            index_url="https://download.pytorch.org/whl/cpu",
        )
        .pip_install_from_requirements(str(ML_DIR / "requirements.txt"))
        .run_commands("python -c " + shlex.quote(BUILD_CODE))
        .env(
            {
                "PYTHONPATH": REMOTE_ROOT,
                "ML_STORAGE_DIR": "/opt/models",
                "ML_DEFAULT_MODEL_REPO": MODEL_REPO,
                "ML_DEFAULT_MODEL_PATH": REMOTE_MODEL,
                "ML_DEFAULT_MODEL_RELEASE": json.dumps(RELEASE),
                "ML_DEPLOYMENT_SHA": os.environ.get("DEPLOYMENT_SHA", "unknown"),
            }
        )
        # Modal exige que add_local_* sea el último paso de la receta.
        .add_local_dir(str(ML_DIR / "app"), f"{REMOTE_ROOT}/app")
    )

app = modal.App(APP_NAME)


@app.function(
    image=image,
    cpu=2.0,
    memory=8192,
    timeout=1800,
    startup_timeout=900,
    scaledown_window=120,
    min_containers=0,
    max_containers=1,
    secrets=[modal.Secret.from_name("historia-viva-ml")],
)
@modal.concurrent(max_inputs=4)
@modal.asgi_app(requires_proxy_auth=True)
def ml_api():
    """Publica sin reescritura la aplicación FastAPI existente."""
    from app.main import app as fastapi_app

    return fastapi_app
