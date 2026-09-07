"""Comparar en validación, evaluar al ganador en test y registrar el candidato.

Uso: python -m app.ml.experiments --dataset snapshot.json --config config.json --output outputs/run
No conecta con producción ni activa modelos.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from app.ml.baselines import _metric_report
from app.ml.experiment_data import fingerprint, validate_snapshot


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def select_best(trials: list[dict]) -> dict:
    # Los empates conservan el orden predefinido. Nunca recibe métricas de test.
    return max(trials, key=lambda trial: trial["validation"]["f1_macro"])


def assess_candidate(metrics: dict, baseline: dict, backend: str) -> dict:
    reasons = []
    labels = metrics.get("labels", [])
    per_class = metrics.get("per_class", [])
    if backend != "beto":
        reasons.append("El servicio de producción carga BETO; TF-IDF es un baseline")
    if metrics["f1_macro"] < 0.70:
        reasons.append("F1 macro inferior a 0.70")
    if len(per_class) != len(labels) or {r["label"] for r in per_class} != set(labels):
        reasons.append("Métricas por clase incompletas")
    elif any(row["f1"] < 0.50 or row["support"] <= 0 for row in per_class):
        reasons.append("Alguna clase tiene F1 inferior a 0.50 o carece de soporte")
    if metrics["f1_macro"] <= baseline["f1_macro"]:
        reasons.append("No supera TF-IDF en el mismo test")
    return {"status": "experimental" if reasons else "eligible_for_review", "reasons": reasons,
            "production_changed": False,
            "next_step": "Comparar con el modelo activo en el mismo conjunto y verificar carga antes de activar"}


def fit_tfidf(train: list[dict], params: dict, seed: int):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    model = Pipeline([
        ("tfidf", TfidfVectorizer(strip_accents="unicode", ngram_range=(1, 2), min_df=2,
                                  max_features=50_000, sublinear_tf=True)),
        ("classifier", LogisticRegression(C=params["C"], class_weight="balanced", max_iter=2000,
                                           random_state=seed, solver="lbfgs")),
    ])
    model.fit([r["text"] for r in train], [r["label"] for r in train])
    return model


def run_experiments(payload: dict, config: dict, output: Path) -> dict:
    audit = validate_snapshot(payload)
    backend = config["backend"]
    if backend not in ("tfidf", "beto"):
        raise ValueError("Backend desconocido")
    configurations = config.get("trials") or []
    ids = [p.get("id", "") for p in configurations]
    if not ids or len(ids) != len(set(ids)) or any(not i or not all(c.isalnum() or c in "-_" for c in i) for i in ids):
        raise ValueError("Cada experimento necesita un id único y seguro")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "dataset-audit.json", audit)
    write_json(output / "configuration.json", config)
    labels = sorted(payload["labels"])
    train = [r for r in payload["items"] if r["split"] == "train"]
    val = [r for r in payload["items"] if r["split"] == "val"]
    seed = config.get("seed", 42)
    trials = []
    for params in configurations:
        print(f"Training {params['id']} ({backend})", flush=True)
        trial_dir = output / params["id"]
        trial_dir.mkdir()
        if backend == "tfidf":
            import joblib
            model = fit_tfidf(train, params, seed)
            predicted = model.predict([r["text"] for r in val]).tolist()
            joblib.dump(model, trial_dir / "model.joblib")
            details = {}
        else:
            from app.ml.beto_experiment import fit_beto
            predicted, details = fit_beto(train, val, labels, params, config, trial_dir)
        metrics = _metric_report([r["label"] for r in val], predicted, labels)
        metrics["split"] = "val"
        trial = {"id": params["id"], "hyperparams": params, "validation": metrics, **details}
        trials.append(trial)
        write_json(trial_dir / "validation.json", trial)
        print(f"Validation F1 macro: {metrics['f1_macro']:.5f}", flush=True)

    best = select_best(trials)
    # Se guarda la decisión ANTES de consultar test.
    write_json(output / "selection.json", {"selected": best["id"], "criterion": "validation_f1_macro", "trials": trials})
    test = [r for r in payload["items"] if r["split"] == "test"]
    if backend == "tfidf":
        import joblib
        selected = joblib.load(output / best["id"] / "model.joblib")  # artefacto creado por esta ejecución
        predicted = selected.predict([r["text"] for r in test]).tolist()
    else:
        from app.ml.beto_experiment import predict_beto
        predicted = predict_beto(output / best["id"], test, labels, best["hyperparams"])
    metrics = _metric_report([r["label"] for r in test], predicted, labels)
    baseline_model = fit_tfidf(train, {"C": 1.0}, seed)
    baseline = _metric_report([r["label"] for r in test], baseline_model.predict([r["text"] for r in test]).tolist(), labels)
    metrics["baseline"] = {"name": "tfidf_logistic_regression", "f1_macro": baseline["f1_macro"],
                           "dataset_sha256": audit["dataset_sha256"]}
    metrics["results_by_source_type"] = {}
    for kind in sorted({r.get("sourceType") or "unknown" for r in test}):
        indices = [i for i, r in enumerate(test) if (r.get("sourceType") or "unknown") == kind]
        metrics["results_by_source_type"][kind] = {"n_samples": len(indices), backend: _metric_report(
            [test[i]["label"] for i in indices], [predicted[i] for i in indices], labels)}
    write_json(output / best["id"] / "metrics.json", metrics)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    versions = {}
    for package in ("numpy", "scikit-learn", "torch", "transformers", "tokenizers"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            pass
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "backend": backend,
              "git_commit": commit, "working_tree_dirty": dirty, "python": platform.python_version(),
              "dependencies": versions, "dataset": payload.get("dataset"), **audit,
              "config_sha256": fingerprint(config), "selected": best["id"], "trials": trials,
              "test": metrics, "baseline_test": baseline,
              "decision": assess_candidate(metrics, baseline, backend)}
    write_json(output / "report.json", report)
    rows = ["# Experimentos ejecutados", "", f"Backend: {backend}. Selección por F1 macro de validación.", "",
            "| Configuración | F1 macro validación |", "|---|---:|"]
    rows += [f"| {t['id']} | {t['validation']['f1_macro']:.5f} |" for t in trials]
    rows += ["", f"Seleccionado: **{best['id']}**. F1 macro test: **{metrics['f1_macro']:.5f}**.",
             f"Baseline fijo TF-IDF en test: {baseline['f1_macro']:.5f}.", "",
             f"Estado: {report['decision']['status']}. Producción no modificada.", "",
             "El test académico ya se utilizó en v1; esta comparación no constituye una evaluación externa nueva."]
    (output / "report.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.dataset).read_text(encoding="utf-8-sig"))
    config = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
    result = run_experiments(payload, config, Path(args.output))
    print(json.dumps({"selected": result["selected"], "test_f1": result["test"]["f1_macro"],
                      "decision": result["decision"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
