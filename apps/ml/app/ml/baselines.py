"""Baselines acadÃ©micos reproducibles para clasificaciÃ³n temÃ¡tica.

El mÃ³dulo evalÃºa un clasificador mayoritario y TF-IDF + regresiÃ³n logÃ­stica
sin modificar el snapshot ni registrar estos modelos como BETO desplegables.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)


def _metric_report(y_true: list[str], y_pred: list[str], labels: list[str]) -> dict:
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    _, _, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="weighted", zero_division=0
    )
    per_p, per_r, per_f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 5),
        "precision_macro": round(float(precision_macro), 5),
        "recall_macro": round(float(recall_macro), 5),
        "f1_macro": round(float(f1_macro), 5),
        "f1_weighted": round(float(f1_weighted), 5),
        "per_class": [
            {
                "label": label,
                "precision": round(float(per_p[index]), 5),
                "recall": round(float(per_r[index]), 5),
                "f1": round(float(per_f1[index]), 5),
                "support": int(support[index]),
            }
            for index, label in enumerate(labels)
        ],
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "labels": labels,
        "split": "test",
    }


def _bootstrap_f1_ci(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str],
    *,
    iterations: int,
    seed: int,
) -> dict:
    """IC percentil del F1 macro mediante remuestreo del conjunto de test."""
    rng = np.random.default_rng(seed)
    size = len(y_true)
    scores = []
    for _ in range(iterations):
        indices = rng.integers(0, size, size=size)
        sampled_true = [y_true[i] for i in indices]
        sampled_pred = [y_pred[i] for i in indices]
        scores.append(
            precision_recall_fscore_support(
                sampled_true,
                sampled_pred,
                labels=labels,
                average="macro",
                zero_division=0,
            )[2]
        )
    low, high = np.percentile(scores, [2.5, 97.5])
    return {
        "method": "bootstrap_percentile_95",
        "iterations": iterations,
        "seed": seed,
        "low": round(float(low), 5),
        "high": round(float(high), 5),
    }


def _require_splits(items: Iterable[dict]) -> dict[str, list[dict]]:
    splits = {name: [] for name in ("train", "val", "test")}
    for item in items:
        split = item.get("split")
        if split in splits:
            splits[split].append(item)
    missing = [name for name, rows in splits.items() if not rows]
    if missing:
        raise ValueError(f"El snapshot no contiene filas en: {', '.join(missing)}")
    return splits


def evaluate_baselines(payload: dict, *, seed: int = 42, bootstrap: int = 2000) -> dict:
    items = payload.get("items") or []
    splits = _require_splits(items)
    labels = sorted(payload.get("labels") or {row["label"] for row in items})
    train_labels = [row["label"] for row in splits["train"]]
    test_labels = [row["label"] for row in splits["test"]]
    test_texts = [row["text"] for row in splits["test"]]

    absent_train = sorted(set(labels) - set(train_labels))
    absent_test = sorted(set(labels) - set(test_labels))
    if absent_train or absent_test:
        raise ValueError(
            f"Cobertura de clases incompleta. train={absent_train or 'OK'}, "
            f"test={absent_test or 'OK'}"
        )

    majority_label = Counter(train_labels).most_common(1)[0][0]
    majority_pred = [majority_label] * len(test_labels)
    majority = _metric_report(test_labels, majority_pred, labels)
    majority["f1_macro_ci95"] = _bootstrap_f1_ci(
        test_labels, majority_pred, labels, iterations=bootstrap, seed=seed
    )

    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=2,
        max_features=50_000,
        sublinear_tf=True,
    )
    x_train = vectorizer.fit_transform([row["text"] for row in splits["train"]])
    x_test = vectorizer.transform(test_texts)
    classifier = LogisticRegression(
        class_weight="balanced",
        max_iter=2_000,
        random_state=seed,
        solver="lbfgs",
    )
    classifier.fit(x_train, train_labels)
    tfidf_pred = classifier.predict(x_test).tolist()
    tfidf = _metric_report(test_labels, tfidf_pred, labels)
    tfidf["f1_macro_ci95"] = _bootstrap_f1_ci(
        test_labels, tfidf_pred, labels, iterations=bootstrap, seed=seed
    )

    by_source_type = {}
    source_types = sorted({row.get("sourceType") for row in splits["test"] if row.get("sourceType")})
    for source_type in source_types:
        indices = [
            index for index, row in enumerate(splits["test"])
            if row.get("sourceType") == source_type
        ]
        by_source_type[source_type] = {
            "n_samples": len(indices),
            "majority": _metric_report(
                [test_labels[index] for index in indices],
                [majority_pred[index] for index in indices],
                labels,
            ),
            "tfidf_logistic_regression": _metric_report(
                [test_labels[index] for index in indices],
                [tfidf_pred[index] for index in indices],
                labels,
            ),
        }

    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "experiment": "baseline_majority_vs_tfidf_logistic_regression",
        "dataset": payload.get("dataset"),
        "dataset_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "seed": seed,
        "split_counts": {name: len(rows) for name, rows in splits.items()},
        "class_distribution": dict(sorted(Counter(row["label"] for row in items).items())),
        "configuration": {
            "tfidf": {
                "ngram_range": [1, 2],
                "min_df": 2,
                "max_features": 50_000,
                "sublinear_tf": True,
                "strip_accents": "unicode",
            },
            "logistic_regression": {
                "class_weight": "balanced",
                "max_iter": 2_000,
                "solver": "lbfgs",
            },
        },
        "results": {"majority": majority, "tfidf_logistic_regression": tfidf},
        "results_by_source_type": by_source_type,
    }


def _read_json(location: str, token: str | None) -> dict:
    if location.startswith(("http://", "https://")):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        with urlopen(Request(location, headers=headers), timeout=60) as response:
            return json.load(response)
    with Path(location).open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="EvalÃºa baselines sobre un snapshot exportado")
    parser.add_argument("input", help="Archivo JSON o URL /api/datasets/:id/export")
    parser.add_argument("--token", help="JWT si la entrada es una URL protegida")
    parser.add_argument("--output", required=True, help="Ruta del informe JSON")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap", type=int, default=2000)
    args = parser.parse_args()

    report = evaluate_baselines(
        _read_json(args.input, args.token), seed=args.seed, bootstrap=args.bootstrap
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["results"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

