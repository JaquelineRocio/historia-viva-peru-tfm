"""Compara una ampliación de train con TF-IDF ya seleccionado; predice solo validación."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/ml"))
from app.ml.experiment_data import fingerprint, validate_snapshot
from app.ml.experiments import fit_tfidf
from app.ml.baselines import _metric_report


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_info(path: Path) -> dict:
    return {"path": path.resolve().relative_to(ROOT).as_posix(),
            "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def validate_inputs(before: dict, after: dict, config: dict, selection: dict) -> dict:
    validate_snapshot(before)
    validate_snapshot(after)
    if (before["labels"] != after["labels"]
            or after["items"][:len(before["items"])] != before["items"]
            or len(after["items"]) <= len(before["items"])
            or any(r["split"] != "train" for r in after["items"][len(before["items"]):])):
        raise ValueError("Solo se admite añadir train, conservando filas anteriores y evaluación")
    trials = [t for t in selection["trials"] if t["id"] == selection["selected"]]
    configs = [p for p in config["trials"] if p["id"] == selection["selected"]]
    if (config["backend"] != "tfidf" or len(trials) != 1 or len(configs) != 1
            or trials[0]["hyperparams"] != configs[0]
            or selection["criterion"] != "validation_f1_macro"):
        raise ValueError("La selección anterior no coincide con la configuración TF-IDF")
    return trials[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "config", "selection", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa una carpeta nueva dentro de outputs/; no se sobrescriben resultados")
    before, after, config, selection = (read(getattr(args, n)) for n in ("before", "after", "config", "selection"))
    chosen = validate_inputs(before, after, config, selection)
    inputs = {name: file_info(getattr(args, name)) for name in ("before", "after", "config", "selection")}
    inputs.update({name: file_info(path) for name, path in (
        ("runner", Path(__file__)), ("trainer", ROOT / "apps/ml/app/ml/experiments.py"),
        ("metrics", ROOT / "apps/ml/app/ml/baselines.py"),
        ("validation", ROOT / "apps/ml/app/ml/experiment_data.py"))})
    import joblib
    from sklearn.exceptions import ConvergenceWarning
    from threadpoolctl import threadpool_limits

    report = {"created_at": datetime.now(timezone.utc).isoformat(), "inputs": inputs,
              "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "working_tree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()),
              "hyperparams": chosen["hyperparams"], "seed": config["seed"],
              "selection_policy": "Use the previous selection unchanged; no new hyperparameter search.",
              "python": platform.python_version(), "thread_limit": 1,
              "dependencies": {p: importlib.metadata.version(p) for p in (
                  "numpy", "scipy", "scikit-learn", "joblib", "threadpoolctl")},
              "runs": {}, "test_predictions_performed": False, "production_changed": False}
    target.mkdir(parents=True, exist_ok=False)
    predictions = {}
    for name, data in (("before", before), ("after", after)):
        train = [r for r in data["items"] if r["split"] == "train"]
        val = [r for r in data["items"] if r["split"] == "val"]
        print(f"Training {name}: {len(train)} rows; C={chosen['hyperparams']['C']}", flush=True)
        started = time.perf_counter()
        with threadpool_limits(limits=1), warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            model = fit_tfidf(train, chosen["hyperparams"], config["seed"])
            predicted = model.predict([r["text"] for r in val]).tolist()
        elapsed = time.perf_counter() - started
        metrics = _metric_report([r["label"] for r in val], predicted, sorted(data["labels"]))
        metrics["split"] = "val"
        if name == "before" and metrics != chosen["validation"]:
            raise ValueError("La versión anterior no reproduce las métricas registradas")
        joblib.dump(model, target / f"{name}.joblib")
        predictions[name] = predicted
        report["runs"][name] = {"dataset_sha256": fingerprint(data), "audit": validate_snapshot(data),
                                "validation": metrics, "fit_and_predict_seconds": round(elapsed, 3),
                                "vocabulary_size": len(model['tfidf'].vocabulary_),
                                "solver_iterations": model['classifier'].n_iter_.tolist(),
                                "model": file_info(target / f"{name}.joblib")}
        print(f"Validation F1 macro: {metrics['f1_macro']:.5f}", flush=True)
    report["validation_predictions_changed"] = sum(a != b for a, b in zip(predictions["before"], predictions["after"]))
    report["delta_validation_f1_macro"] = round(report["runs"]["after"]["validation"]["f1_macro"]
                                                - report["runs"]["before"]["validation"]["f1_macro"], 5)
    report["before_reproduced_previous_metrics"] = True
    report["evaluation_sha256"] = fingerprint([r for r in after["items"] if r["split"] != "train"])
    for name, payload in (("report.json", report), ("validation-predictions.json", predictions)):
        (target / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"delta_validation_f1_macro": report["delta_validation_f1_macro"],
                      "predictions_changed": report["validation_predictions_changed"],
                      "test_predictions_performed": False}), flush=True)


if __name__ == "__main__":
    main()
