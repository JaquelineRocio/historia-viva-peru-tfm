"""Diagnóstico TF-IDF dejando fuera cada fuente de train; no evalúa val/test."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import subprocess
import time
import warnings
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from compare_tfidf_validation import ROOT, file_info, read, previous_validation
from app.ml.experiment_data import fingerprint, validate_snapshot
from app.ml.experiments import fit_tfidf
from app.ml.baselines import _metric_report


def make_folds(train: list[dict], labels: list[str]) -> list[dict]:
    if not train or any(r["split"] != "train" for r in train):
        raise ValueError("Solo se aceptan filas de train")
    sources = sorted({r["resourceId"] for r in train})
    if len(sources) < 2 or any(not s for s in sources):
        raise ValueError("Se requieren al menos dos fuentes identificadas")
    folds = []
    for source in sources:
        fit = [i for i, r in enumerate(train) if r["resourceId"] != source]
        evaluation = [i for i, r in enumerate(train) if r["resourceId"] == source]
        if set(labels) != {train[i]["label"] for i in fit}:
            raise ValueError("Una ronda carece de clases en entrenamiento; revisar cobertura")
        # El duplicado conocido de la misma fuente queda unido en una ronda.
        normalized = lambda r: " ".join(r["text"].casefold().split())
        if {normalized(train[i]) for i in fit} & {normalized(train[i]) for i in evaluation}:
            raise ValueError("Texto exacto compartido entre fuentes de la ronda")
        folds.append(dict(source_id=source, fit_indices=fit, evaluation_indices=evaluation))
    return folds


def metrics(truth: list[str], predicted: list[str], labels: list[str]) -> dict:
    result = _metric_report(truth, predicted, labels)
    result["split"] = "internal_train_source_holdout"
    return result


def validate_configuration(data: dict, config: dict, selection: dict, previous: dict) -> dict:
    trials = [t for t in selection["trials"] if t["id"] == selection["selected"]]
    params = [t for t in config["trials"] if t["id"] == selection["selected"]]
    if (config["backend"] != "tfidf" or selection["criterion"] != "validation_f1_macro"
            or len(trials) != 1 or len(params) != 1 or trials[0]["hyperparams"] != params[0]):
        raise ValueError("Configuración distinta de la selección previa")
    previous_validation(previous, data, config, trials[0])
    return params[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dataset", "config", "selection", "previous-report", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa una carpeta nueva dentro de outputs/; no se sobrescribe")
    data, config, selection, previous = (read(getattr(args, n)) for n in ("dataset", "config", "selection", "previous_report"))
    audit = validate_snapshot(data)
    params = validate_configuration(data, config, selection, previous)
    inputs = {n: file_info(getattr(args, n)) for n in ("dataset", "config", "selection", "previous_report")}
    inputs.update({n: file_info(p) for n, p in (
        ("runner", Path(__file__)), ("trainer", ROOT / "apps/ml/app/ml/experiments.py"),
        ("metrics", ROOT / "apps/ml/app/ml/baselines.py"), ("validation", ROOT / "apps/ml/app/ml/experiment_data.py"),
        ("comparison_helpers", ROOT / "scripts/compare_tfidf_validation.py"))})
    if (inputs["dataset"]["file_sha256"] != previous["inputs"]["after"]["file_sha256"]
            or any(inputs[n]["file_sha256"] != previous["inputs"][n]["file_sha256"]
                   for n in ("config", "selection", "trainer", "metrics", "validation"))):
        raise ValueError("Dataset, configuración o implementación distintos del informe previo")
    rows = [(i, row) for i, row in enumerate(data["items"]) if row["split"] == "train"]
    train = [r for _, r in rows]
    labels = sorted(data["labels"])
    folds = make_folds(train, labels)
    import joblib
    from sklearn.exceptions import ConvergenceWarning
    from threadpoolctl import threadpool_limits

    report = dict(created_at=datetime.now(timezone.utc).isoformat(), inputs=inputs,
                  git_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                  working_tree_dirty=bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()),
                  hyperparams=params, seed=config["seed"], thread_limit=1, python=platform.python_version(),
                  dependencies={p: importlib.metadata.version(p) for p in ("numpy", "scipy", "scikit-learn", "joblib", "threadpoolctl")},
                  dataset_sha256=fingerprint(data), train_sha256=fingerprint(train), audit=audit,
                  evaluation_sha256=fingerprint([r for r in data["items"] if r["split"] != "train"]),
                  protocol="Leave one existing training source out; fit vocabulary and classifier from scratch on other training sources. Fixed prior hyperparameters.",
                  metric_policy="Macro F1 always uses all seven labels, including classes absent from an individual evaluation source. Pooled metrics weight rows, not sources.",
                  folds=[], validation_predictions_performed=False, test_predictions_performed=False,
                  production_changed=False, hyperparameter_search_performed=False)
    target.mkdir(parents=True, exist_ok=False)
    predictions = [None] * len(train)
    for number, fold in enumerate(folds, 1):
        fit = [train[i] for i in fold["fit_indices"]]
        evaluation = [train[i] for i in fold["evaluation_indices"]]
        counts = Counter(r["label"] for r in fit)
        majority = min(counts, key=lambda label: (-counts[label], label))
        started = time.perf_counter()
        with threadpool_limits(limits=1), warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            model = fit_tfidf(fit, params, config["seed"])
            predicted = model.predict([r["text"] for r in evaluation]).tolist()
        elapsed = time.perf_counter() - started
        model_path = target / f"fold-{number:02}.joblib"
        joblib.dump(model, model_path)
        truth = [r["label"] for r in evaluation]
        score = metrics(truth, predicted, labels)
        fold_report = dict(source_id=fold["source_id"], fit_count=len(fit), evaluation_count=len(evaluation),
                           fit_sources=sorted({r["resourceId"] for r in fit}),
                           fit_class_counts=dict(counts), evaluation_class_counts=dict(Counter(truth)),
                           absent_evaluation_classes=sorted(set(labels)-set(truth)),
                           fit_sha256=fingerprint(fit), evaluation_sha256=fingerprint(evaluation),
                           tfidf=score, majority=metrics(truth, [majority]*len(truth), labels), majority_label=majority,
                           vocabulary_size=len(model['tfidf'].vocabulary_), solver_iterations=model['classifier'].n_iter_.tolist(),
                           fit_and_predict_seconds=round(elapsed, 3), model=file_info(model_path))
        report["folds"].append(fold_report)
        for index, prediction in zip(fold["evaluation_indices"], predicted):
            if predictions[index] is not None:
                raise ValueError("Una fila fue evaluada más de una vez")
            predictions[index] = dict(dataset_index=rows[index][0], source_id=train[index]["resourceId"],
                                      text_sha256=fingerprint(train[index]["text"]), actual=train[index]["label"],
                                      predicted=prediction, majority_predicted=majority)
        print(f"Fold {number}/{len(folds)}: {len(evaluation)} rows, accuracy={score['accuracy']:.5f}", flush=True)
        del model
    if any(p is None for p in predictions):
        raise ValueError("Faltan predicciones internas")
    report["pooled_tfidf"] = metrics([p["actual"] for p in predictions], [p["predicted"] for p in predictions], labels)
    report["pooled_majority"] = metrics([p["actual"] for p in predictions], [p["majority_predicted"] for p in predictions], labels)
    report["each_train_row_evaluated_once"] = True
    report["equal_source_mean_accuracy"] = round(sum(f["tfidf"]["accuracy"] for f in report["folds"])/len(folds), 5)
    for entry in inputs.values():
        if file_info(ROOT / entry["path"])["file_sha256"] != entry["file_sha256"]:
            raise ValueError("Cambió una entrada durante el diagnóstico")
    for name, payload in (("report.json", report), ("predictions.json", predictions)):
        (target / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"folds": len(folds), "rows": len(predictions), "pooled_f1_macro": report["pooled_tfidf"]["f1_macro"]}), flush=True)


if __name__ == "__main__":
    main()
