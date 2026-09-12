"""Contrato de versiones publicadas; utilidades sin dependencias de ML."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

MODEL_FILES = (
    "config.json", "labels.json", "model.safetensors", "special_tokens_map.json",
    "tokenizer.json", "tokenizer_config.json", "vocab.txt",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_release(value: dict, *, published: bool = True) -> dict:
    if value.get("schema_version") != 1:
        raise ValueError("Versión de manifiesto desconocida")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", value.get("repo_id", "")):
        raise ValueError("Repositorio de modelo inválido")
    if published and not re.fullmatch(r"[0-9a-f]{40}", value.get("revision", "")):
        raise ValueError("Se requiere el SHA completo de la revisión de Hugging Face")
    files = value.get("files", {})
    if set(files) != set(MODEL_FILES):
        raise ValueError("Lista de archivos de inferencia incompleta o inesperada")
    if any(not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{64}", v) for v in files.values()):
        raise ValueError("Hash de archivo inválido")
    labels = value.get("labels")
    if (not isinstance(labels, list) or len(labels) != 7
            or any(not isinstance(v, str) or not v for v in labels) or len(set(labels)) != 7):
        raise ValueError("Se requieren siete etiquetas distintas y ordenadas")
    if type(value.get("max_len")) is not int or not 1 <= value["max_len"] <= 512:
        raise ValueError("Longitud de inferencia inválida")
    return value


def read_release(path: Path) -> dict:
    return validate_release(json.loads(path.read_text(encoding="utf-8")))


def verify_files(folder: Path, release: dict) -> None:
    for name, expected in release["files"].items():
        if sha256(folder / name) != expected:
            raise ValueError(f"Hash incorrecto: {name}")
    meta = json.loads((folder / "labels.json").read_text(encoding="utf-8"))
    config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
    mapping = {str(i): label for i, label in enumerate(release["labels"])}
    if meta.get("id2label") != mapping or config.get("id2label") != mapping:
        raise ValueError("El orden de las etiquetas no coincide con la cabeza del modelo")
    if meta.get("max_len") != release["max_len"]:
        raise ValueError("Longitud de inferencia diferente a la versión registrada")


def identity(release: dict) -> dict:
    # Identifica también tokenizer, etiquetas y longitud, no solo los pesos.
    return {key: release[key] for key in ("repo_id", "revision", "files", "labels", "max_len")}


def download_release(release: dict, target: Path) -> None:
    from huggingface_hub import snapshot_download

    validate_release(release)
    target.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=release["repo_id"], revision=release["revision"],
                      local_dir=str(target), allow_patterns=list(MODEL_FILES), token=False)
    verify_files(target, release)
