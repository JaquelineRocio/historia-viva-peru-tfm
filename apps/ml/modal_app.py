"""Despliegue serverless del servicio ML en Modal.

Uso desde la raíz del repositorio:
    modal deploy apps/ml/modal_app.py

El secreto `historia-viva-ml` debe contener ML_INTERNAL_TOKEN. El modelo BETO
público se incorpora a la imagen durante el build para reducir el arranque en frío.
"""
from pathlib import Path

import modal


APP_NAME = "historia-viva-peru-ml"
MODEL_REPO = "Jaqueline98/historia-viva-beto-v1"
REMOTE_ROOT = "/opt/historia-viva-ml"
REMOTE_MODEL = "/opt/models/beto-v1"
ML_DIR = Path(__file__).resolve().parent


image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "torch==2.12.0",
        index_url="https://download.pytorch.org/whl/cpu",
    )
    .pip_install_from_requirements(str(ML_DIR / "requirements.txt"))
    .run_commands(
        "python -c \"from huggingface_hub import snapshot_download; "
        f"snapshot_download(repo_id='{MODEL_REPO}', local_dir='{REMOTE_MODEL}')\""
    )
    .env(
        {
            "PYTHONPATH": REMOTE_ROOT,
            "ML_STORAGE_DIR": "/opt/models",
            "ML_DEFAULT_MODEL_REPO": MODEL_REPO,
            "ML_DEFAULT_MODEL_PATH": REMOTE_MODEL,
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
