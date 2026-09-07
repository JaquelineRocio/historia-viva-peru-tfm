import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ml.experiment_data import validate_snapshot
from app.ml.experiments import assess_candidate, run_experiments, select_best
from app.ml.maintenance import prepare_snapshot, run_maintenance


def snapshot():
    return {"labels": ["a", "b"], "items": [
        {"text": f"{'caballo guerra' if label == 'a' else 'barco comercio'} {split} ejemplo {i}",
         "label": label, "split": split, "resourceId": split, "sourceType": "pdf"}
        for split in ("train", "val", "test") for label in ("a", "b") for i in range(3)
    ]}


def test_rejects_source_leakage():
    data = snapshot()
    data["items"][-1]["resourceId"] = "train"
    with pytest.raises(ValueError, match="fuente"):
        validate_snapshot(data)


def test_rejects_duplicate_text_between_splits():
    data = snapshot()
    data["items"][-1]["text"] = data["items"][0]["text"].upper()
    with pytest.raises(ValueError, match="duplicado"):
        validate_snapshot(data)


@pytest.mark.parametrize("split", ["val", "test"])
def test_rejects_missing_class_in_evaluation(split):
    data = snapshot()
    data["items"] = [r for r in data["items"] if not (r["split"] == split and r["label"] == "b")]
    with pytest.raises(ValueError, match=split):
        validate_snapshot(data)


def test_selection_does_not_use_test_scores():
    trials = [{"id": "a", "validation": {"f1_macro": .8}, "test": {"f1_macro": .1}},
              {"id": "b", "validation": {"f1_macro": .7}, "test": {"f1_macro": .99}}]
    assert select_best(trials)["id"] == "a"


def test_complete_pipeline_preserves_dataset_and_never_promotes_tfidf(tmp_path):
    data = snapshot()
    before = copy.deepcopy(data)
    result = run_experiments(data, {"backend": "tfidf", "trials": [{"id": "c1", "C": 1}]}, tmp_path / "run")
    assert data == before
    assert result["test"]["f1_macro"] == 1
    assert result["decision"]["status"] == "experimental"
    assert result["decision"]["production_changed"] is False
    selection = json.loads((tmp_path / "run" / "selection.json").read_text())
    assert selection["criterion"] == "validation_f1_macro"
    assert "test" not in selection["trials"][0]
    with pytest.raises(FileExistsError):
        run_experiments(data, {"backend": "tfidf", "trials": [{"id": "c1", "C": 1}]}, tmp_path / "run")


def test_quality_gate_requires_every_class_and_beating_baseline():
    metrics = {"labels": ["a", "b"], "f1_macro": .8,
               "per_class": [{"label": "a", "f1": .8, "support": 10}]}
    assert assess_candidate(metrics, {"f1_macro": .3}, "beto")["status"] == "experimental"
    metrics["per_class"].append({"label": "b", "f1": .8, "support": 10})
    assert assess_candidate(metrics, {"f1_macro": .85}, "beto")["status"] == "experimental"
    assert assess_candidate(metrics, {"f1_macro": .3}, "beto")["status"] == "eligible_for_review"


def test_maintenance_preserves_evaluation_despite_changed_labels_and_splits():
    original = snapshot()
    reviewed = copy.deepcopy(original)
    reviewed["items"][0]["label"] = "b"
    reviewed["items"][-1]["label"] = "a"
    for row in reviewed["items"]:
        row["split"] = "train"
    candidate, changes = prepare_snapshot(original, reviewed)
    assert [r for r in candidate["items"] if r["split"] != "train"] == [r for r in original["items"] if r["split"] != "train"]
    assert changes["relabeled"] == 1
    assert changes["changed_examples"] == 1


def test_maintenance_skips_unchanged_data_without_training(tmp_path):
    report = run_maintenance(snapshot(), snapshot(), {}, tmp_path / "run")
    assert report["status"] == "skipped"
    assert not (tmp_path / "run/experiment").exists()


def test_maintenance_runs_on_new_reviewed_data(tmp_path):
    original = snapshot()
    reviewed = copy.deepcopy(original)
    reviewed["items"].append({"text": "caballo guerra evidencia nueva", "label": "a", "resourceId": "new", "sourceType": "pdf", "split": "val"})
    report = run_maintenance(original, reviewed, {"backend": "tfidf", "trials": [{"id": "c1", "C": 1}]}, tmp_path / "run", min_changes=1)
    assert report["maintenance"]["added"] == 1
    assert report["split_counts"] == {"train": 7, "val": 6, "test": 6}
    assert report["decision"]["production_changed"] is False
    assert (tmp_path / "run" / report["selected"] / "model.joblib").is_file()
