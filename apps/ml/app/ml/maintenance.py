"""Preparar reentrenamiento desde un export completo de datos revisados.

Conserva las fuentes de evaluación del snapshot de referencia. Los cambios de
etiquetas en evaluación se registran pero no se incorporan a entrenamiento.
El export debe ser completo: la ausencia de un ejemplo de train significa retiro.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from app.ml.experiment_data import fingerprint, validate_snapshot
from app.ml.experiments import run_experiments, write_json


def _key(row):
    return fingerprint([row["resourceId"], " ".join(row["text"].casefold().split())])


def prepare_snapshot(reference: dict, reviewed: dict) -> tuple[dict, dict]:
    validate_snapshot(reference)
    if sorted(reference["labels"]) != sorted(reviewed.get("labels", [])):
        raise ValueError("Cambió la taxonomía; se necesita un protocolo de evaluación nuevo")
    holdout = [copy.deepcopy(r) for r in reference["items"] if r["split"] != "train"]
    held_sources = {r["resourceId"] for r in holdout}
    old_train = {_key(r): r for r in reference["items"] if r["split"] == "train"}
    new_train = {}
    held_reviewed = []
    for row in reviewed.get("items", []):
        if not row.get("resourceId") or row.get("label") not in reference["labels"] or not isinstance(row.get("text"), str) or not row["text"].strip():
            raise ValueError("Export revisado incompleto o inválido")
        if row["resourceId"] in held_sources:
            held_reviewed.append(row)
            continue
        key = _key(row)
        if key in new_train and new_train[key]["label"] != row["label"]:
            raise ValueError("Un mismo fragmento tiene etiquetas contradictorias")
        new_train[key] = {"text": row["text"], "label": row["label"], "resourceId": row["resourceId"],
                          "sourceType": row.get("sourceType"), "split": "train"}
    added = len(new_train.keys() - old_train.keys())
    removed = len(old_train.keys() - new_train.keys())
    relabeled = sum(old_train[k]["label"] != new_train[k]["label"] for k in old_train.keys() & new_train.keys())
    train_rows = [new_train[k] for k in sorted(new_train)]
    content_hash = fingerprint(train_rows + holdout)
    snapshot = {"dataset": {"name": f"maintenance-{content_hash[:12]}",
                            "reference_sha256": fingerprint(reference), "reviewed_sha256": fingerprint(reviewed),
                            "evaluation_sha256": fingerprint(holdout), "content_sha256": content_hash},
                "labels": reference["labels"], "items": train_rows + holdout}
    audit = validate_snapshot(snapshot)
    change = {"added": added, "removed": removed, "relabeled": relabeled,
              "changed_examples": added + removed + relabeled, "evaluation_sha256": fingerprint(holdout),
              "heldout_rows_ignored_from_reviewed_export": len(held_reviewed), "audit": audit}
    return snapshot, change


def run_maintenance(reference, reviewed, config, output: Path, min_changes=20):
    if min_changes < 1:
        raise ValueError("min_changes debe ser positivo")
    snapshot, changes = prepare_snapshot(reference, reviewed)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "changes.json", changes)
    write_json(output / "snapshot.json", snapshot)
    if changes["changed_examples"] < min_changes:
        report = {"status": "skipped", "reason": "insufficient_changes", "min_changes": min_changes,
                  "changes": changes, "production_changed": False}
        write_json(output / "report.json", report)
        (output / "report.md").write_text(
            f"# Mantenimiento omitido\n\nCambios: {changes['changed_examples']}. Mínimo requerido: {min_changes}.\n",
            encoding="utf-8")
        return report
    report = run_experiments(snapshot, config, output / "experiment")
    report["selected"] = "experiment/" + report["selected"]
    report["maintenance"] = changes
    write_json(output / "report.json", report)
    (output / "report.md").write_text((output / "experiment/report.md").read_text(encoding="utf-8"), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--reviewed", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-changes", type=int, default=20)
    args = parser.parse_args()
    read = lambda path: json.loads(Path(path).read_text(encoding="utf-8-sig"))
    report = run_maintenance(read(args.reference), read(args.reviewed), read(args.config), Path(args.output), args.min_changes)
    print(json.dumps({"status": report.get("status", "evaluated"), "selected": report.get("selected")}), flush=True)


if __name__ == "__main__":
    main()
