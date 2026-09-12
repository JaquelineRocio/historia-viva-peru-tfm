"""Prepara/verifica BETO y, con publish, publica una versión y actualiza su selección.

No entrena, no lee corpus, no ejecuta Git ni despliega Modal.
"""
from __future__ import annotations

import argparse
import gc
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/ml"))
from app.ml.model_release import MODEL_FILES, sha256, validate_release, verify_files

DEFAULT_CHECKPOINT = ROOT / "outputs/beto-v3/phase-c/seed-42/R2/checkpoint-8"
DEFAULT_CARD = ROOT / "deploy/huggingface-r2/README.md"
MANIFEST = ROOT / "configs/production-model.json"
DEFAULT_REPO = "Jaqueline98/historia-viva-beto-r2-42"
AUTH_HELP = (
    "Ejecuta .\\outputs\\venv-ml\\Scripts\\hf.exe auth login en tu terminal "
    "con un token de Hugging Face que permita escribir en el repositorio. "
    "Comprueba la cuenta con hf.exe auth whoami. "
    "Si HF_TOKEN o HUGGING_FACE_HUB_TOKEN están definidos, prevalecen sobre la sesión guardada."
)
SMOKE_TEXTS = [
    "La Constitución organiza los poderes y las instituciones de la república.",
    "El ejército inició la campaña militar y libró una batalla por la independencia del Perú.",
    "Las comunidades indígenas participaron en las movilizaciones regionales.",
    "Esta receta de cocina explica cómo preparar una sopa de verduras.",
    ("El documento describe los antecedentes coloniales y sus instituciones. " * 90)
    + "La campaña militar terminó con la batalla.",
]


class PublicationError(Exception):
    """Mensaje operativo sin respuesta del servidor ni credenciales."""


def check_auth(api) -> None:
    """Consulta de solo lectura antes de copiar pesos o inferir."""
    try:
        account = api.whoami()
    except Exception as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in (401, 403):
            raise PublicationError("Hugging Face rechazó la autenticación. " + AUTH_HELP) from None
        raise PublicationError("No se pudo comprobar la sesión de Hugging Face. Revisa la conexión e inténtalo de nuevo.") from None
    role = account.get("auth", {}).get("accessToken", {}).get("role")
    if role == "read":
        raise PublicationError("El token solo permite lectura. " + AUTH_HELP)
    # Los permisos fine-grained se comprueban en la operación de escritura.


def authenticated_api():
    from huggingface_hub import HfApi, get_token
    if not get_token():
        raise PublicationError("No hay una credencial de Hugging Face disponible. " + AUTH_HELP)
    api = HfApi()
    check_auth(api)
    return api


def reuse_package(package: Path) -> tuple[Path, dict]:
    """Reutiliza el recibo local solo si los siete archivos siguen siendo idénticos."""
    package = package.resolve()
    receipt = package.parent / f"{package.name}-verification.json"
    if not receipt.is_file():
        raise PublicationError("No existe el recibo de verificación del paquete; ejecuta prepare primero.")
    saved = json.loads(receipt.read_text(encoding="utf-8"))
    release = validate_release(saved["release"], published=False)
    result = saved.get("verification", {})
    if (result.get("passed") is not True or result.get("tokenization_equal") is not True
            or result.get("texts") != len(SMOKE_TEXTS)
            or len(result.get("predictions", [])) != len(SMOKE_TEXTS)):
        raise PublicationError("El recibo no acredita una comprobación de paridad completa.")
    source = saved.get("source_files", {})
    if any(source.get(name) != release["files"][name] for name in MODEL_FILES if name != "labels.json"):
        raise PublicationError("El recibo no conserva la identidad del checkpoint original.")
    verify_files(package, release)
    if not (package / "README.md").is_file():
        raise PublicationError("Falta la ficha del modelo en el paquete.")
    return package, release


def write_json(path: Path, value: dict) -> None:
    """Reemplazo atómico: nunca deja la selección de producción a medio escribir."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     suffix=".tmp", delete=False) as stream:
        tmp = Path(stream.name)
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    try:
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def prepare(checkpoint: Path, output: Path, repo_id: str, card: Path) -> tuple[Path, dict, dict]:
    checkpoint, output = checkpoint.resolve(), output.resolve()
    if checkpoint == output or checkpoint in output.parents or output in checkpoint.parents:
        raise ValueError("La entrega debe estar separada del checkpoint original")
    config = json.loads((checkpoint / "config.json").read_text(encoding="utf-8"))
    meta = json.loads((checkpoint / "labels.json").read_text(encoding="utf-8"))
    mapping = config["id2label"]
    labels = [mapping[str(i)] for i in range(len(mapping))]
    if "labels" in meta and meta["labels"] != labels:
        raise ValueError("labels.json no coincide con el orden del checkpoint")
    if "id2label" in meta and meta["id2label"] != mapping:
        raise ValueError("id2label no coincide con el checkpoint")
    lengths = [meta[k] for k in ("max_length", "max_len") if k in meta]
    if not lengths or len(set(lengths)) != 1:
        raise ValueError("Longitud de inferencia ausente o contradictoria")
    source_hashes = {name: sha256(checkpoint / name) for name in MODEL_FILES}
    # Una carpeta única conserva entregas anteriores y evita mezclar archivos ajenos.
    output.mkdir(parents=True, exist_ok=True)
    package = Path(tempfile.mkdtemp(prefix="beto-", dir=output))
    for name in MODEL_FILES:
        if name != "labels.json":
            shutil.copyfile(checkpoint / name, package / name)
    write_json(package / "labels.json", {"id2label": mapping, "max_len": lengths[0]})
    shutil.copyfile(card, package / "README.md")
    release = validate_release({
        "schema_version": 1, "repo_id": repo_id,
        "files": {name: sha256(package / name) for name in MODEL_FILES},
        "labels": labels, "max_len": lengths[0],
    }, published=False)
    verify_files(package, release)
    # Detecta un checkpoint modificado mientras se copiaba.
    if source_hashes != {name: sha256(checkpoint / name) for name in MODEL_FILES}:
        raise ValueError("El checkpoint cambió durante el empaquetado")
    for name in MODEL_FILES:
        if name != "labels.json" and release["files"][name] != source_hashes[name]:
            raise ValueError(f"La copia alteró {name}")
    return package, release, source_hashes


def smoke(checkpoint: Path, package: Path, release: dict) -> dict:
    """CPU y textos sintéticos: paridad de tokenización y predicciones, no calidad histórica."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from app.ml import beto

    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
    packaged_tokenizer = AutoTokenizer.from_pretrained(package, local_files_only=True)
    options = dict(truncation=True, padding=True, max_length=release["max_len"], return_tensors="pt")
    original_inputs = tokenizer(SMOKE_TEXTS, **options)
    packaged_inputs = packaged_tokenizer(SMOKE_TEXTS, **options)
    if (set(original_inputs) != set(packaged_inputs)
            or any(not torch.equal(original_inputs[k], packaged_inputs[k]) for k in original_inputs)):
        raise ValueError("La tokenización del paquete cambió")
    model = AutoModelForSequenceClassification.from_pretrained(checkpoint, local_files_only=True).eval()
    with torch.inference_mode():
        probabilities = torch.softmax(model(**original_inputs).logits, dim=-1)
        confidence, indices = probabilities.max(dim=-1)
    expected = [{"label": release["labels"][ix], "confidence": round(float(c), 4)}
                for ix, c in zip(indices.tolist(), confidence.tolist())]
    del model
    gc.collect()
    try:
        beto.load_model(str(package))
        actual = beto.infer(SMOKE_TEXTS)
        if actual != expected:
            raise ValueError("Las predicciones del servicio difieren del checkpoint original")
    finally:
        beto._active = None
        gc.collect()
    verify_files(package, release)
    return {"passed": True, "device": "cpu", "texts": len(SMOKE_TEXTS),
            "tokenization_equal": True, "predictions": actual,
            "scope": "Paridad de empaquetado; textos sintéticos, sin evaluación de corpus"}


def publish(package: Path, release: dict, manifest: Path, *, api=None, download=None) -> dict:
    """La selección solo cambia tras verificar la revisión remota, sin autenticación."""
    validate_release(release, published=False)
    if api is None:
        api = authenticated_api()
    if download is None:
        from huggingface_hub import hf_hub_download
        download = hf_hub_download
    verify_files(package, release)
    api.create_repo(repo_id=release["repo_id"], repo_type="model", private=False, exist_ok=True)
    info = api.model_info(release["repo_id"])
    if info.private or info.gated:
        raise ValueError("Modal está configurado para modelos públicos sin acceso restringido")
    commit = api.upload_folder(
        repo_id=release["repo_id"], repo_type="model", folder_path=str(package),
        allow_patterns=[*MODEL_FILES, "README.md"],
        commit_message="Publish verified BETO inference package",
        parent_commit=info.sha,
    )
    selected = validate_release({**release, "revision": commit.oid})
    # Guarda el recibo antes de verificar red; una incidencia nunca activa la versión.
    write_json(package.parent / f"{package.name}-upload.json", selected)
    for name, expected in selected["files"].items():
        remote = download(repo_id=selected["repo_id"], revision=selected["revision"],
                          filename=name, token=False)
        if sha256(Path(remote)) != expected:
            raise ValueError(f"El archivo remoto no coincide: {name}")
    verify_files(package, selected)
    if manifest.exists():
        previous = json.loads(manifest.read_text(encoding="utf-8"))
        validate_release(previous)
        write_json(manifest.parent / "model-releases" / f"{previous['revision']}.json", previous)
    write_json(manifest.parent / "model-releases" / f"{selected['revision']}.json", selected)
    write_json(manifest, selected)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "publish"])
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    source.add_argument("--package", type=Path, help="Reutiliza un paquete y su recibo sin repetir inferencias")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/model-releases")
    parser.add_argument("--repo-id")
    parser.add_argument("--model-card", type=Path)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()
    if args.package and (args.command != "publish" or args.model_card):
        parser.error("--package se usa con publish, sin --model-card")
    if args.model_card is None and args.checkpoint.resolve() != DEFAULT_CHECKPOINT.resolve():
        parser.error("Para otro checkpoint especifica --model-card con sus resultados y limitaciones")
    api = authenticated_api() if args.command == "publish" else None
    if args.package:
        package, release = reuse_package(args.package)
        if args.repo_id and args.repo_id != release["repo_id"]:
            parser.error("--repo-id difiere del repositorio del paquete verificado")
        print(f"Paquete verificado reutilizado: {package}", flush=True)
    else:
        package, release, source_hashes = prepare(
            args.checkpoint, args.output, args.repo_id or DEFAULT_REPO, args.model_card or DEFAULT_CARD)
        print(f"Paquete: {package}", flush=True)
        verification = smoke(args.checkpoint, package, release)
        if source_hashes != {name: sha256(args.checkpoint / name) for name in MODEL_FILES}:
            raise ValueError("El original cambió durante la verificación")
        write_json(package.parent / f"{package.name}-verification.json", {
            "release": release, "source_files": source_hashes, "verification": verification,
        })
    if args.command == "publish":
        selected = publish(package, release, args.manifest, api=api)
        print(f"Publicado {selected['repo_id']} @ {selected['revision']}")
        print(f"Selección actualizada: {args.manifest}. Revisa los cambios y haz tu commit/push.")
    else:
        print("Preparación y paridad verificadas. Sin publicación ni cambio de modelo en producción.")


def cli() -> int:
    try:
        main()
    except PublicationError as exc:
        print(f"Publicación detenida: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status not in (401, 403):
            raise
        reason = "Autenticación rechazada (401)." if status == 401 else "Permisos insuficientes para el repositorio (403)."
        print(f"Publicación detenida: {reason} {AUTH_HELP}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
