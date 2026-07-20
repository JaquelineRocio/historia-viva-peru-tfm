import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ml.baselines import evaluate_baselines


LABELS = ["a", "b"]


def _payload():
    items = []
    for split in ("train", "val", "test"):
        for index in range(4):
            label = LABELS[index % 2]
            word = "caballo" if label == "a" else "barco"
            items.append({"text": f"{word} historia ejemplo {index}", "label": label, "split": split})
    return {"dataset": {"id": "snapshot"}, "labels": LABELS, "items": items}


def test_baselines_are_reproducible_and_report_both_models():
    first = evaluate_baselines(_payload(), seed=7, bootstrap=20)
    second = evaluate_baselines(_payload(), seed=7, bootstrap=20)

    assert first == second
    assert first["split_counts"] == {"train": 4, "val": 4, "test": 4}
    assert set(first["results"]) == {"majority", "tfidf_logistic_regression"}
    assert first["results"]["tfidf_logistic_regression"]["f1_macro"] == 1.0


def test_missing_split_is_rejected():
    payload = _payload()
    payload["items"] = [row for row in payload["items"] if row["split"] != "test"]

    with pytest.raises(ValueError, match="test"):
        evaluate_baselines(payload, bootstrap=5)
