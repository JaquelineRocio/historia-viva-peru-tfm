"""Compara BETO con el checkpoint previo, offline y solo en validación."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

# Antes de que Transformers/Hugging Face se importen, incluso indirectamente.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from check_beto_readiness import ROOT, check, file_info, memory, read
from app.ml.experiment_data import fingerprint, validate_snapshot
from app.ml.baselines import _metric_report
from app.ml.beto_experiment import fit_beto, predict_beto


def info(path: Path) -> dict:
    return {"path": path.resolve().relative_to(ROOT).as_posix(), **file_info(path)}


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def verify_readiness(data: dict, expected: dict, current: dict, dataset: str = "reviewed") -> None:
    if dataset not in ("reviewed", "reference"):
        raise ValueError("Dataset no admitido")
    if (expected["status"] != "prerequisites_checked_runner_pending"
            or not expected["verification"]["passed"]
            or current["status"] != "prerequisites_checked_runner_pending"
            or current["recipe"] != expected["recipe"]
            or current["cache"] != expected["cache"]
            or current["baseline"] != expected["baseline"]
            or current["packages"] != expected["packages"]):
        raise ValueError("Prerrequisitos o receta distintos de la preparación revisada")
    if (fingerprint(data) != expected[f"{dataset}_audit"]["dataset_sha256"]
            or fingerprint([r for r in data["items"] if r["split"] != "train"]) != expected["evaluation_sha256"]):
        raise ValueError("Dataset o evaluación distintos de la preparación")
    validate_snapshot(data)


def compare(data: dict, readiness: dict, baseline: Path, output: Path) -> tuple[dict, dict]:
    """Solo entrega train/val al entrenador; el checkpoint previo se carga sin ajustar."""
    train = [r for r in data["items"] if r["split"] == "train"]
    val = [r for r in data["items"] if r["split"] == "val"]
    if not train or not val:
        raise ValueError("Se requieren train y validación")
    labels = sorted(data["labels"])
    recipe = readiness["recipe"]
    params = recipe["hyperparams"]
    config = {k: recipe[k] for k in ("base_model", "revision", "seed")}
    truth = [r["label"] for r in val]
    print("Reproducing previous BETO validation", flush=True)
    before = predict_beto(baseline, val, labels, params)
    before_metrics = _metric_report(truth, before, labels)
    before_metrics["split"] = "val"
    if before_metrics != readiness["baseline"]["validation"]:
        raise ValueError("El checkpoint anterior no reproduce sus métricas; no se entrena")
    write(output / "baseline-validation.json", dict(metrics=before_metrics, predictions=before))
    candidate_path = output / "candidate"
    candidate_path.mkdir(exist_ok=False)
    print(f"Training one fixed BETO configuration on {len(train)} rows", flush=True)
    predicted, details = fit_beto(train, val, labels, params, config, candidate_path)
    if (details["resolved_revision"] != recipe["revision"]
            or len(details["history"]) != params["epochs"]
            or details["best_epoch"] != max(details["history"], key=lambda e: e["validation_f1_macro"])["epoch"]):
        raise ValueError("Revisión base o selección de época distintas del protocolo")
    metrics = _metric_report(truth, predicted, labels)
    metrics["split"] = "val"
    if metrics["f1_macro"] != max(e["validation_f1_macro"] for e in details["history"]):
        raise ValueError("Las predicciones no corresponden a la época seleccionada")
    restored = predict_beto(candidate_path, val, labels, params)
    if restored != predicted:
        raise ValueError("El candidato guardado no reproduce sus predicciones")
    report = dict(before_validation=before_metrics, after_validation=metrics, training_details=details,
                  delta_validation_f1_macro=round(metrics["f1_macro"]-before_metrics["f1_macro"], 5),
                  predictions_changed=sum(a != b for a, b in zip(before, predicted)),
                  baseline_metrics_reproduced=True, saved_candidate_predictions_reproduced=True,
                  training_configurations=1, learning_rate_search_performed=False,
                  test_predictions_performed=False, production_changed=False)
    return report, dict(before=before, after=predicted)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dataset", choices=("reviewed", "reference"), default="reviewed",
                        help="reference reproduce el entrenamiento original; reviewed compara los datos revisados")
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa una carpeta nueva dentro de outputs/; no se sobrescribe")
    expected = read(args.readiness)
    # Cotejar archivos antes de importar/cargar los pesos para inferencia.
    entries = list(expected["inputs"].values()) + expected["baseline"]["files"]
    for entry in entries:
        if file_info(ROOT / entry["path"])["file_sha256"] != entry["file_sha256"]:
            raise ValueError(f"Entrada alterada: {entry['path']}")
    current = check()
    data = read(ROOT / expected["inputs"][args.dataset]["path"])
    verify_readiness(data, expected, current, args.dataset)
    baseline = (ROOT / next(e["path"] for e in expected["baseline"]["files"] if e["name"] == "model.safetensors")).parent
    import torch
    torch.set_num_threads(4)
    target.mkdir(parents=True, exist_ok=False)
    write(target / "resource-check.json", current)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    try:
        report, predictions = compare(data, expected, baseline, target)
        report.update(created_at=datetime.now(timezone.utc).isoformat(),
                      dataset_role=args.dataset,
                      purpose="reference_retraining_control" if args.dataset == "reference" else "reviewed_data_comparison",
                      training_input=info(ROOT / expected["inputs"][args.dataset]["path"]),
                      git_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                      working_tree_dirty=bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()),
                      inputs={"readiness": info(args.readiness), "runner": info(Path(__file__)),
                              **{k: info(ROOT / expected["inputs"][k]["path"]) for k in ("reviewed", "trainer", "reference")}},
                      recipe=expected["recipe"], packages=current["packages"], python=current["python"],
                      audit=validate_snapshot(data), dataset_sha256=fingerprint(data),
                      evaluation_sha256=expected["evaluation_sha256"], offline=True, downloads_performed=False,
                      elapsed_comparison_seconds=round(time.perf_counter()-started, 2),
                      cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                      cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(), ram_after=memory(),
                      candidate_files=[info(p) for p in sorted((target / "candidate").iterdir()) if p.is_file()])
        for entry in entries:
            if file_info(ROOT / entry["path"])["file_sha256"] != entry["file_sha256"]:
                raise ValueError("Cambió una entrada durante la comparación")
        write(target / "report.json", report)
        write(target / "validation-predictions.json", predictions)
        print(json.dumps({"before_f1": report["before_validation"]["f1_macro"],
                          "after_f1": report["after_validation"]["f1_macro"], "test_predictions_performed": False}), flush=True)
    except Exception as exc:
        write(target / "failure.json", dict(status="failed", error_type=type(exc).__name__,
                                            message=str(exc), test_predictions_performed=False, production_changed=False))
        raise


if __name__ == "__main__":
    main()
