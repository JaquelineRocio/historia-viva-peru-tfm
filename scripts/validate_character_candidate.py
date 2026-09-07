"""Ajusta el candidato de caracteres ya elegido y compara solo validación."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import subprocess
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

from evaluate_tfidf_by_source import fit_representation
from compare_tfidf_validation import ROOT, file_info, read, verify_files
from app.ml.experiment_data import fingerprint, validate_snapshot
from app.ml.baselines import _metric_report


def validate_inputs(data: dict, candidate: dict, word: dict) -> None:
    validate_snapshot(data)
    if (candidate["representation"] != "char_wb"
            or candidate["vectorizer"]["ngram_range"] != [3, 5]
            or candidate["interpretation"]["next_candidate"] != "char_wb_3_5_C4"
            or not candidate["verification"]["passed"]
            or candidate["hyperparams"] != word["hyperparams"]
            or candidate["hyperparams"] != {"id": "tfidf-c4", "C": 4.0}
            or candidate["seed"] != word["seed"] or candidate["seed"] != 42):
        raise ValueError("No coincide el candidato previamente elegido")
    holdout = [r for r in data["items"] if r["split"] != "train"]
    if (fingerprint(data) != candidate["dataset_sha256"]
            or fingerprint(data) != word["runs"]["after"]["dataset_sha256"]
            or fingerprint(holdout) != candidate["evaluation_sha256"]
            or fingerprint(holdout) != word["evaluation_sha256"]
            or word["runs"]["after"]["validation"]["split"] != "val"):
        raise ValueError("Dataset o evaluación distintos de los experimentos previos")


def val_metrics(truth: list[str], predicted: list[str], labels: list[str]) -> dict:
    result = _metric_report(truth, predicted, labels)
    result["split"] = "val"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dataset", "candidate-evidence", "word-report", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa una carpeta nueva dentro de outputs/; no se sobrescribe")
    data, candidate, word = (read(getattr(args, n)) for n in ("dataset", "candidate_evidence", "word_report"))
    validate_inputs(data, candidate, word)
    inputs = {n: file_info(getattr(args, n)) for n in ("dataset", "candidate_evidence", "word_report")}
    inputs.update({n: file_info(path) for n, path in (
        ("runner", Path(__file__)), ("representation_trainer", ROOT / "scripts/evaluate_tfidf_by_source.py"),
        ("comparison_helpers", ROOT / "scripts/compare_tfidf_validation.py"),
        ("metrics", ROOT / "apps/ml/app/ml/baselines.py"), ("validation", ROOT / "apps/ml/app/ml/experiment_data.py"))})
    if (inputs["dataset"]["file_sha256"] != candidate["inputs"]["dataset"]["file_sha256"]
            or inputs["dataset"]["file_sha256"] != word["inputs"]["after"]["file_sha256"]
            or inputs["representation_trainer"]["file_sha256"] != candidate["inputs"]["runner"]["file_sha256"]):
        raise ValueError("Dataset o implementación distintos del candidato interno")
    verify_files(candidate["outputs"] + word["outputs"] + [word["runs"]["after"]["model"]])
    for name in ("metrics", "validation"):
        if any(inputs[name]["file_sha256"] != r["inputs"][name]["file_sha256"] for r in (candidate, word)):
            raise ValueError("Cambió la implementación de las métricas o validación")
    import joblib
    from sklearn.exceptions import ConvergenceWarning
    from threadpoolctl import threadpool_limits

    train = [r for r in data["items"] if r["split"] == "train"]
    val = [r for r in data["items"] if r["split"] == "val"]
    labels, truth = sorted(data["labels"]), [r["label"] for r in val]
    baseline = joblib.load(ROOT / word["runs"]["after"]["model"]["path"])
    with threadpool_limits(limits=1):
        word_predictions = baseline.predict([r["text"] for r in val]).tolist()
    word_metrics = val_metrics(truth, word_predictions, labels)
    paths = [e["path"] for e in word["outputs"] if Path(e["path"]).name == "validation-predictions.json"]
    if (len(paths) != 1 or read(ROOT / paths[0])["after"] != word_predictions
            or word_metrics != word["runs"]["after"]["validation"]):
        raise ValueError("El modelo de palabras no reproduce las predicciones y métricas previas")
    print(f"Baseline verified; training char_wb on {len(train)} rows", flush=True)
    started = time.perf_counter()
    with threadpool_limits(limits=1), warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        model = fit_representation(train, candidate["hyperparams"], candidate["seed"], "char_wb")
        char_predictions = model.predict([r["text"] for r in val]).tolist()
    elapsed = time.perf_counter() - started
    if model["classifier"].get_params() != baseline["classifier"].get_params():
        raise ValueError("Cambió la configuración del clasificador")
    char_metrics = val_metrics(truth, char_predictions, labels)
    target.mkdir(parents=True, exist_ok=False)
    joblib.dump(model, target / "character.joblib")
    report = dict(created_at=datetime.now(timezone.utc).isoformat(), inputs=inputs,
                  git_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                  working_tree_dirty=bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()),
                  python=platform.python_version(), thread_limit=1,
                  dependencies={p: importlib.metadata.version(p) for p in ("numpy", "scipy", "scikit-learn", "joblib", "threadpoolctl")},
                  dataset_sha256=fingerprint(data), audit=validate_snapshot(data),
                  evaluation_sha256=fingerprint([r for r in data["items"] if r["split"] != "train"]),
                  hyperparams=candidate["hyperparams"], seed=candidate["seed"], vectorizer=candidate["vectorizer"],
                  word_validation=word_metrics, character_validation=char_metrics,
                  delta_validation_f1_macro=round(char_metrics["f1_macro"]-word_metrics["f1_macro"], 5),
                  validation_predictions_changed=sum(a != b for a, b in zip(word_predictions, char_predictions)),
                  character_model=file_info(target / "character.joblib"), word_model=word["runs"]["after"]["model"],
                  fit_and_predict_seconds=round(elapsed, 3), solver_iterations=model["classifier"].n_iter_.tolist(),
                  vocabulary_size=len(model["tfidf"].vocabulary_), new_fits=1,
                  baseline_predictions_reproduced=True, test_predictions_performed=False, production_changed=False,
                  hyperparameter_search_performed=False)
    verify_files(list(inputs.values()))
    for name, payload in (("report.json", report), ("validation-predictions.json", dict(word=word_predictions, character=char_predictions))):
        (target / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"word_f1": word_metrics["f1_macro"], "character_f1": char_metrics["f1_macro"],
                      "character_accuracy": char_metrics["accuracy"], "test_predictions_performed": False}), flush=True)


if __name__ == "__main__":
    main()
