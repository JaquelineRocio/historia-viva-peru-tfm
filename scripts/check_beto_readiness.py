"""Revisa BETO local sin descargas, entrenamiento ni predicciones históricas."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/ml"))
from app.ml.experiment_data import fingerprint, validate_snapshot


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_info(path: Path) -> dict:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return dict(name=path.name, bytes=path.stat().st_size, file_sha256=h.hexdigest())


def memory() -> dict | None:
    if os.name != "nt":
        return None
    class Status(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong) for name in ("total", "available", "page_total", "page_available",
                                                   "virtual_total", "virtual_available", "extended")]
    s = Status()
    s.length = ctypes.sizeof(s)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s)):
        raise OSError("No se pudo consultar la memoria física")
    return dict(total_bytes=s.total, available_bytes=s.available, load_percent=s.load)


def select_recipe(config: dict, selection: dict, previous: dict, reference: dict, reviewed: dict) -> dict:
    validate_snapshot(reference)
    validate_snapshot(reviewed)
    matching = [t for t in selection["trials"] if t["id"] == selection["selected"]]
    params = [t for t in config["trials"] if t["id"] == selection["selected"]]
    if len(matching) != 1 or len(params) != 1:
        raise ValueError("La selección debe identificar una única receta")
    if (config["backend"] != "beto" or selection["criterion"] != "validation_f1_macro"
            or fingerprint(config) != previous["config_sha256"]
            or config["base_model"] != matching[0]["base_model"]
            or matching[0]["hyperparams"] != params[0]
            or previous["selected"] != selection["selected"]
            or next((t for t in previous["trials"] if t["id"] == selection["selected"]), None) != matching[0]
            or config["revision"] != matching[0]["resolved_revision"]):
        raise ValueError("La receta no coincide con la selección BETO anterior")
    evaluation = lambda d: [r for r in d["items"] if r["split"] != "train"]
    if (fingerprint(reference) != previous["dataset_sha256"]
            or reference["labels"] != reviewed["labels"] or evaluation(reference) != evaluation(reviewed)):
        raise ValueError("La referencia, taxonomía o evaluación no coinciden")
    return matching[0]


def check() -> dict:
    paths = {"config": ROOT / "configs/experiments/beto.json",
             "selection": ROOT / "artifacts/experiments/course-u1/beto/selection.json",
             "previous_report": ROOT / "artifacts/experiments/course-u1/beto/report.json",
             "reference": ROOT / "artifacts/datasets/gold-v1-source-aware.json",
             "reviewed": ROOT / "outputs/villanueva-snapshot-v1/reviewed-export.json",
             "trainer": ROOT / "apps/ml/app/ml/beto_experiment.py",
             "general_runner": ROOT / "apps/ml/app/ml/experiments.py", "checker": Path(__file__)}
    inputs = {k: {"path": p.relative_to(ROOT).as_posix(), **file_info(p)} for k, p in paths.items()}
    config, selection, previous, reference, reviewed = [read(paths[k]) for k in ("config", "selection", "previous_report", "reference", "reviewed")]
    selected = select_recipe(config, selection, previous, reference, reviewed)
    # Bloqueo explícito de red antes de importar Hugging Face/Transformers.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    packages = {p: importlib.metadata.version(p) for p in (
        "torch", "transformers", "tokenizers", "safetensors", "huggingface-hub", "numpy", "scikit-learn")}
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from huggingface_hub.constants import HF_HUB_CACHE

    cuda = dict(available=torch.cuda.is_available(), torch_cuda=torch.version.cuda, matmul_passed=False)
    if cuda["available"]:
        cuda.update(name=torch.cuda.get_device_name(0), free_total_bytes=list(torch.cuda.mem_get_info()))
        a = torch.ones((128, 128), device="cuda")
        b = a @ a
        torch.cuda.synchronize()
        cuda["matmul_passed"] = bool(b[0, 0].item() == 128)
        del a, b
        torch.cuda.empty_cache()
    snapshot = Path(HF_HUB_CACHE) / ("models--" + config["base_model"].replace("/", "--")) / "snapshots" / config["revision"]
    files = ["config.json", "pytorch_model.bin", "special_tokens_map.json", "tokenizer.json", "tokenizer_config.json", "vocab.txt"]
    missing = [n for n in files if not (snapshot / n).is_file()]
    cache_files = [file_info(snapshot / n) for n in files if (snapshot / n).is_file()]
    tokenizer_ok = False
    if not missing:
        tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
        encoded = tokenizer("Comprobación técnica local.", padding="max_length", truncation=True,
                            max_length=selected["hyperparams"]["max_len"], return_tensors="pt")
        tokenizer_ok = list(encoded["input_ids"].shape) == [1, selected["hyperparams"]["max_len"]]
    baseline_dir = ROOT / "outputs/experiments/beto-u1" / selected["id"]
    baseline_names = ["model.safetensors", "config.json", "labels.json", "validation.json",
                      "special_tokens_map.json", "tokenizer.json", "tokenizer_config.json", "vocab.txt"]
    missing_baseline = [n for n in baseline_names if not (baseline_dir / n).is_file()]
    baseline_files = [dict(path=(baseline_dir / n).relative_to(ROOT).as_posix(), **file_info(baseline_dir / n))
                      for n in baseline_names if (baseline_dir / n).is_file()]
    baseline_metadata_ok = False
    if not missing_baseline:
        label_map = read(baseline_dir / "labels.json")
        baseline_metadata_ok = (read(baseline_dir / "validation.json") == selected
                                and label_map["id2label"] == {str(i): label for i, label in enumerate(sorted(reviewed["labels"]))}
                                and label_map["max_len"] == selected["hyperparams"]["max_len"])
    versions_match = all(packages.get(k) == v for k, v in previous["dependencies"].items())
    for key, path in paths.items():
        if file_info(path)["file_sha256"] != inputs[key]["file_sha256"]:
            raise ValueError("Cambió una entrada durante la comprobación")
    ready = cuda["matmul_passed"] and tokenizer_ok and baseline_metadata_ok and versions_match
    return dict(schema_version=1, created_at=datetime.now(timezone.utc).isoformat(),
                status="prerequisites_checked_runner_pending" if ready else "prerequisites_incomplete",
                inputs=inputs, python=platform.python_version(), packages=packages,
                previous_dependency_versions_match=versions_match, ram=memory(),
                disk_free_bytes=shutil.disk_usage(ROOT).free, cuda=cuda,
                cache=dict(model=config["base_model"], revision=config["revision"], files=cache_files,
                           missing=missing, offline_tokenizer_passed=tokenizer_ok),
                baseline=dict(files=baseline_files, missing=missing_baseline, metadata_matches=baseline_metadata_ok,
                              validation=selected["validation"], best_epoch=selected["best_epoch"],
                              historical_training_seconds=selected["seconds"], predictions_reproduced=False),
                recipe=dict(base_model=config["base_model"], revision=config["revision"], seed=config["seed"],
                            hyperparams=selected["hyperparams"], epoch_selection="Best validation F1 among the same three epochs; no new learning-rate search.",
                            optimizer="AdamW", weight_decay=0.01, effective_batch_size=16,
                            gradient_checkpointing=True, mixed_precision=True),
                reference_audit=validate_snapshot(reference), reviewed_audit=validate_snapshot(reviewed),
                evaluation_sha256=fingerprint([r for r in reviewed["items"] if r["split"] != "train"]),
                required_runner="Dedicated validation-only runner; general run_experiments automatically predicts test and must not be used for this comparison.",
                training_performed=False, historical_predictions_performed=False, downloads_performed=False,
                production_changed=False,
                limits=["CUDA kernel and tokenizer checked; model weights hashed but not loaded or trained.",
                        "Free RAM/VRAM are a transient observation, not proof that fine-tuning will fit.",
                        "Previous 84.58-second training is historical, not an estimate guaranteed for the next run."])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    target = parser.parse_args().output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa un archivo nuevo dentro de outputs/; no se sobrescribe")
    report = check()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({k: report[k] for k in ("status", "previous_dependency_versions_match", "training_performed")}))


if __name__ == "__main__":
    main()
