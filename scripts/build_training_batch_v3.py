"""Apply the approved v3 training changes to a new, local experimental copy.

No downloads, model calls or writes outside a new outputs directory. Evaluation
rows are handled only by mechanical equality/hash checks, never for selection.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/ml"))
from app.ml.experiment_data import fingerprint, validate_snapshot  # noqa: E402

BASE = "outputs/corpus-snapshot-v2/reviewed-export.json"
BOUNDARY = "artifacts/reviews/boundary-resolution-v3.json"
BATCH = "artifacts/reviews/training-batch-v3.json"
UNITS = "outputs/boundary-resolution-v3/proposed-replacements.json"
PARENT_ARCHIVE = "outputs/corpus-snapshot-v2/replacement-archive.json"
PINNED = {
    BASE: "5de9ea1a4be3c9d628da51cdf1d07108f43e0ac8ee580acb483013c6dc27c35c",
    BOUNDARY: "1e0f7c55df5a4863b8b263a72fae88da6de541851bd7843192a4d1d1fb679be8",
    BATCH: "b42860373a22f56490871b626a845b32d61f67108998fdc530e2883b57297692",
    UNITS: "8b0f6b6a9b49d16f6615e66ad92ef28a740f8e6de3a1fd498ecc6c7916d37ed9",
    PARENT_ARCHIVE: "dac743647c4ca2715b4e915475dcae999a41f00264243ad64500eeaa5a173777",
}
REPLACEMENTS = {68: "PER-R68-RURAL", 69: "PER-R69-DEC", 552: "BAS-552",
                556: "BAS-556", 558: "BAS-558-social", 560: "BAS-558-norma",
                562: "BAS-562", 564: "BAS-564", 565: "BAS-565"}
QUARANTINE = {298, 532, 548, 559, 561, 763, 765}
WORKS = {"contreras": "doi:10.18800/historica.201102.004",
         "hunefeldt": "doi:10.18800/historica.197902.004",
         "arguedas": "doi:10.18800/conexion.202201.003",
         "hampe": "https://bdigital.uncu.edu.ar/8023",
         "moran": "doi:10.5209/hics.64491"}
FRANCISCA = "arguedas-francisca-author-01"
FRANCISCA_SHA = "cae127746c6d05daafebf45af2cb6e411c72ff2f0623f917b7ebc113e3c6178d"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_sha(text: str) -> str:
    return sha(text.encode("utf-8"))


def normalized(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.casefold())
    return " ".join(re.findall(r"\w+", "".join(c for c in value if not unicodedata.combining(c))))


def content_verified(review: dict) -> None:
    content = {k: v for k, v in review.items() if k != "content_sha256"}
    require(review.get("content_sha256") == fingerprint(content), "Review content_sha256 mismatch")


def output_target(path: Path) -> Path:
    target = path.resolve()
    require(target.is_relative_to((ROOT / "outputs").resolve()) and not target.exists(),
            "Destination must be a new directory inside outputs/")
    return target


class Inputs:
    def __init__(self) -> None:
        self.records: dict[str, dict] = {}

    def read(self, name: str, expected: str | None = None, *, as_json: bool = True):
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT), "Input path outside workspace")
        relative = path.relative_to(ROOT).as_posix()
        require(relative.startswith(("outputs/", "artifacts/reviews/", "scripts/")),
                "Input path is not an authorized evidence or builder path")
        data = path.read_bytes()
        actual = sha(data)
        require(expected is None or actual == expected, f"Input file hash mismatch: {relative}")
        self.records[relative] = {"path": relative, "file_sha256": actual, "bytes": len(data)}
        return json.loads(data) if as_json else data

    def unchanged(self) -> None:
        for name, entry in self.records.items():
            require(sha((ROOT / name).read_bytes()) == entry["file_sha256"], f"Input changed: {name}")


def check_actions(base: dict, boundary: dict, proposal: dict, batch: dict) -> tuple[dict, list]:
    actions = boundary["proposed_actions"]
    by_index = {a["index"]: a for a in actions}
    require(len(by_index) == len(actions) == 16 and set(by_index) == set(REPLACEMENTS) | QUARANTINE,
            "Unexpected or duplicate action indices")
    units = {u["id"]: u for u in proposal["units"]}
    require(len(units) == len(proposal["units"]) == 9 and set(units) == set(REPLACEMENTS.values()),
            "Unexpected replacement inventory")
    for index, action in by_index.items():
        row = base["items"][index]
        require(row["split"] == "train" and text_sha(row["text"]) == action["before_sha256"] and
                row["label"] == action["before_label"] and row["resourceId"] == action["resource_id"] and
                row["sourceType"] == action["source_type"] and len(row["text"].split()) == action["before_words"],
                f"Original row does not match approved action: {index}")
        if index in QUARANTINE:
            require(action["action"] == "quarantine_from_future_training_copy" and
                    action.get("converted_to_no_relevante") is False, "Unexpected quarantine action")
            continue
        unit = units[REPLACEMENTS[index]]
        require(action["action"] == "replace_or_relabel_in_future_copy" and
                action["candidate_id"] == unit["id"] and unit["placement_index_in_future_copy"] == index and
                unit["sha256"] == text_sha(unit["text"]) == action["after_sha256"] and
                unit["proposed_label"] == action["after_label"] and
                unit["words"] == len(unit["text"].split()) == action["after_words"] and
                120 <= unit["words"] <= 250 and unit["ordinary_length_pass"] is True and
                action["text_changes"] == (row["text"] != unit["text"]) and
                action["label_changes"] == (row["label"] != unit["proposed_label"]),
                f"Replacement differs from approved action: {index}")
    gate = boundary["earlier_batch_gate"]
    require(gate["input"] == BATCH and gate["retained_pending"] == ["HUN-03B"] and
            gate["remaining_proposed"] == 30 and len(batch["additions"]) == 31,
            "Unexpected previous-batch gate")
    require(len({u["id"] for u in batch["additions"]}) == 31, "Duplicate addition IDs")
    additions = [u for u in batch["additions"] if u["id"] != "HUN-03B"]
    require(len(additions) == 30 and set(batch["sources"]) == set(WORKS) and
            set(u["source_key"] for u in additions) == set(WORKS), "Unexpected additions or works")
    for unit in additions:
        words = len(unit["text"].split())
        require(text_sha(unit["text"]) == unit["text_sha256"] and words == unit["words"] and
                unit["proposed_label"] in base["labels"] and
                unit["status"] == "proposed_addition_not_applied" and
                not unit.get("additional_condition_before_training"), "Unapproved addition")
        if unit["id"] == FRANCISCA:
            require(words == 114 and unit["text_sha256"] == FRANCISCA_SHA and
                    unit["length_exception"] == {"sha256": FRANCISCA_SHA, "word_count": 114},
                    "The nominal 114-word exception changed")
        else:
            require(120 <= words <= 250 and not unit.get("length_exception"), "Unexpected length exception")
    return by_index, additions


def exact_overlaps(items: list, changed_indices: set[int]) -> list[list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for i, row in enumerate(items):
        groups[normalized(row["text"])].append(i)
    duplicates = [indices for indices in groups.values() if len(indices) > 1]
    require(not any(changed_indices.intersection(indices) for indices in duplicates),
            "A replacement/addition has an exact normalized overlap")
    return duplicates


def build() -> tuple[dict, dict, dict, Inputs]:
    inputs = Inputs()
    base, boundary, batch, proposal, prior_archive = [inputs.read(p, PINNED[p])
                                                    for p in [BASE, BOUNDARY, BATCH, UNITS, PARENT_ARCHIVE]]
    content_verified(boundary)
    content_verified(batch)
    before_audit = validate_snapshot(base)
    require(before_audit["split_counts"] == {"train": 596, "val": 81, "test": 137} and
            len(base["items"]) == 814, "Unexpected parent counts")
    require(fingerprint(prior_archive) == base["dataset"]["replacement_history"][-1]["archive_sha256"],
            "Previous archive is not the one recorded in parent metadata")
    actions, additions = check_actions(base, boundary, proposal, batch)
    # Verify all declared evidence bytes; embed only context/provenance JSON, never full PDFs.
    evidence_payloads = {}
    for review in (boundary, batch):
        for entry in review["local_evidence"]:
            raw = inputs.read(entry["path"], entry["sha256"], as_json=False)
            if entry["path"].endswith(".json") and any(marker in entry["path"] for marker in
                    ("boundary-resolution-v3/", "hampe/raw-pages", "hampe/inventory-unlabelled",
                     "source-moran-layout-pages", "source-moran-inventory")):
                evidence_payloads[entry["path"]] = json.loads(raw)
    for unit in additions:
        entry = unit.get("extraction_evidence")
        if entry:
            evidence_payloads[entry["path"]] = inputs.read(entry["path"], entry.get("sha256", entry.get("file_sha256")))
    pereyra = evidence_payloads["outputs/boundary-resolution-v3/pereyra-review.json"]
    for key in ("originals_archive", "partition_archive", "context_archive"):
        path = pereyra[key]
        evidence_payloads[path] = inputs.read(path)
    preserved = evidence_payloads["outputs/boundary-resolution-v3/originals-preserved.json"]["rows"]
    require(len(preserved) == 16 and {r["index"] for r in preserved} == set(actions), "Original archive map changed")
    require(all({k: v for k, v in r.items() if k != "index"} == base["items"][r["index"]]
                for r in preserved), "Original archive does not equal parent rows")
    updated = copy.deepcopy(base)
    rows, mapping, provenance, changed = [], [], [], set()
    units = {u["id"]: u for u in proposal["units"]}
    for index, row in enumerate(base["items"]):
        entry = {"parent_index": index, "new_index": None, "index_base": 0}
        if index in QUARANTINE:
            entry["action"] = "quarantine_archived_outside_train"
        else:
            new = copy.deepcopy(row)
            entry.update(new_index=len(rows), action="unchanged")
            if index in REPLACEMENTS:
                unit = units[REPLACEMENTS[index]]
                new.update(text=unit["text"], label=unit["proposed_label"])
                entry.update(action="replace_or_relabel", candidate_id=unit["id"])
                changed.add(len(rows))
                provenance.append({"candidate_id": unit["id"], "unit_id": unit["id"],
                    "resource_id": new["resourceId"], "text_sha256": unit["sha256"], "label": new["label"],
                    "parent_index": index, "index_in_this_snapshot": len(rows), "index_base": 0,
                    "snapshot_generation": "corpus-snapshot-v3", "review_path": BOUNDARY,
                    "review_file_sha256": PINNED[BOUNDARY], "decision": copy.deepcopy(actions[index]),
                    "source_provenance": {k: copy.deepcopy(v) for k, v in unit.items() if k != "text"},
                    "annotation_origin": "ai_reviews_with_root_adjudication", "human_expert_validation": False})
            rows.append(new)
        mapping.append(entry)
    resource_ids = {key: str(uuid5(NAMESPACE_URL, "historia-viva-peru:training-work:" + identity))
                    for key, identity in WORKS.items()}
    require(len(set(resource_ids.values())) == 5 and
            not set(resource_ids.values()).intersection(r["resourceId"] for r in base["items"]),
            "New work identity collides with an existing source")
    for unit in additions:
        index = len(rows)
        resource = resource_ids[unit["source_key"]]
        rows.append({"text": unit["text"], "label": unit["proposed_label"], "split": "train",
                     "resourceId": resource, "sourceType": "pdf"})
        changed.add(index)
        provenance.append({"candidate_id": unit["id"], "unit_id": unit["id"], "resource_id": resource,
            "source_group": WORKS[unit["source_key"]], "text_sha256": unit["text_sha256"],
            "label": unit["proposed_label"], "parent_index": None, "index_in_this_snapshot": index,
            "index_base": 0, "snapshot_generation": "corpus-snapshot-v3", "review_path": BATCH,
            "review_file_sha256": PINNED[BATCH], "boundary_gate_path": BOUNDARY,
            "boundary_gate_file_sha256": PINNED[BOUNDARY],
            "source_provenance": {k: copy.deepcopy(v) for k, v in unit.items() if k != "text"},
            "annotation_origin": "ai_reviews_with_root_adjudication", "human_expert_validation": False})
    updated["items"] = rows
    require(len(rows) == 837 and len(provenance) == len(changed) == 39, "Unexpected output size")
    require(all(rows[m["new_index"]] == base["items"][m["parent_index"]]
                for m in mapping if m["action"] == "unchanged"), "An unaffected row changed")
    holdout_before = [r for r in base["items"] if r["split"] != "train"]
    holdout_after = [r for r in rows if r["split"] != "train"]
    require(holdout_after == holdout_before and len(holdout_after) == 218 and
            updated["labels"] == base["labels"], "Evaluation or taxonomy changed")
    duplicates = exact_overlaps(rows, changed)
    require(Counter(normalized(r["text"]) for r in rows if r["split"] == "train") -
            Counter(normalized(r["text"]) for r in base["items"] if r["split"] == "train") ==
            Counter(normalized(rows[i]["text"]) for i in changed if i !=
                    next(p["index_in_this_snapshot"] for p in provenance if p["candidate_id"] == "BAS-562")),
            "Unexpected text multiplicities")
    archive = {"status": "archived_for_local_experimental_application", "parent_file_sha256": PINNED[BASE],
        "parent_dataset_metadata": copy.deepcopy(base["dataset"]),
        "originals": [{"parent_index": i, "row": copy.deepcopy(base["items"][i]),
                       "text_sha256": text_sha(base["items"][i]["text"]), "action": copy.deepcopy(a)}
                      for i, a in sorted(actions.items())],
        "quarantined_indices": sorted(QUARANTINE), "converted_to_no_relevante": False,
        "selected_replacements": copy.deepcopy(proposal["units"]), "selected_additions": copy.deepcopy(additions),
        "withheld_additions": [copy.deepcopy(u) for u in batch["additions"] if u["id"] == "HUN-03B"],
        "row_mapping": mapping, "prior_archives": [{"path": PARENT_ARCHIVE,
            "file_sha256": PINNED[PARENT_ARCHIVE], "canonical_json_sha256": fingerprint(prior_archive),
            "payload": prior_archive}], "evidence_payloads": evidence_payloads,
        "boundary_review": boundary, "batch_review": batch,
        "context_policy": "Full originals, residuals and rejected proposals remain outside train; earlier status fields are historical, approved actions above govern application."}
    metadata = updated["dataset"]
    metadata.update(id=str(uuid5(NAMESPACE_URL, fingerprint(base) + ":training-batch-v3:" + PINNED[BOUNDARY] + PINNED[BATCH])),
                    name="Experimental: lote diverso y fronteras históricas v3", status="experimental_local",
                    parent_sha256=fingerprint(base))
    metadata["added_rows_provenance"].extend(provenance)
    for key, resource in resource_ids.items():
        metadata["source_registry"][resource] = {**copy.deepcopy(batch["sources"][key]),
            "resource_id": resource, "assigned_split": "train", "source_group": WORKS[key],
            "source_key": key, "application_review": BATCH, "application_review_file_sha256": PINNED[BATCH]}
    metadata["replacement_history"].append({"plan": BOUNDARY, "plan_file_sha256": PINNED[BOUNDARY],
        "addition_plan": BATCH, "addition_plan_file_sha256": PINNED[BATCH],
        "parent_sha256": fingerprint(base), "parent_file_sha256": PINNED[BASE],
        "affected_parent_indices": sorted(actions), "rows_replaced_in_place": 9, "text_replacements": 8,
        "label_changes": 9, "retired_parent_indices": sorted(QUARANTINE), "removed_rows": 16,
        "added_rows": 39, "net_new_rows": 23, "new_sources": 5, "archive": "replacement-archive.json",
        "archive_sha256": fingerprint(archive), "archive_hash_kind": "canonical_json_sha256",
        "coverage_reduced_in_selected_training_rows": True})
    metadata["parent_archive_dependencies"].append({"path": PARENT_ARCHIVE,
        "file_sha256": PINNED[PARENT_ARCHIVE], "canonical_json_sha256": fingerprint(prior_archive),
        "embedded_in": "replacement-archive.json:prior_archives"})
    metadata["training_batch_v3"] = {"document_groups": copy.deepcopy(batch["document_groups"]),
        "boundary_sources_and_rights": copy.deepcopy(boundary["sources"]),
        "rights_unresolved": copy.deepcopy(batch["rights_unresolved"]),
        "index_note": "Prior provenance indices refer to their historical snapshots; use current row_mapping and text hashes.",
        "training_performed_by_builder": False, "production_changed": False,
        "public_redistribution_authorized": False, "human_expert_validation": False}
    mutable = {"id", "name", "status", "parent_sha256", "source_registry", "added_rows_provenance",
               "replacement_history", "parent_archive_dependencies"}
    require(all(metadata[k] == v for k, v in base["dataset"].items() if k not in mutable) and
            all(metadata["source_registry"][k] == v for k, v in base["dataset"]["source_registry"].items()) and
            metadata["added_rows_provenance"][:-39] == base["dataset"]["added_rows_provenance"] and
            metadata["replacement_history"][:-1] == base["dataset"]["replacement_history"] and
            metadata["parent_archive_dependencies"][:-1] == base["dataset"]["parent_archive_dependencies"],
            "Previous metadata was modified")
    audit = validate_snapshot(updated)
    require(audit["split_counts"] == {"train": 619, "val": 81, "test": 137} and
            audit["class_distribution"]["train"] == boundary["simulation_only"]["classes_if_combined"] and
            len(audit["sources_by_split"]["train"]) == len(before_audit["sources_by_split"]["train"]) + 5,
            "Final counts, class distribution or source count differs from approval")
    inputs.read("scripts/build_training_batch_v3.py", as_json=False)
    report = {"status": "experimental_local_verified", "parent_file_sha256": PINNED[BASE],
        "parent_sha256": fingerprint(base), "reviewed_sha256": fingerprint(updated),
        "evaluation_sha256": fingerprint(holdout_after), "evaluation_rows_identical": 218,
        "archive_sha256": fingerprint(archive), "hash_kind": "canonical_json_sha256", "audit": audit,
        "input_files": list(inputs.records.values()), "review_content_hashes_verified": True,
        "replaced_in_place": 9, "text_replacements": 8, "label_changes": 9, "quarantined_rows": 7,
        "added_rows": 30, "withheld_addition_ids": ["HUN-03B"], "resource_ids": resource_ids,
        "new_sources": 5, "unaffected_original_rows_identical_and_order_preserved": 798,
        "row_mapping": mapping, "provenance": provenance,
        "normalized_exact_overlap_alerts_for_changed_rows": 0,
        "preexisting_unchanged_duplicate_groups_in_new_indices": duplicates,
        "overlap_scope": "39 changed/added units against all retained items and each other; normalized exact equality only. This is not proof of semantic or documentary independence.",
        "nominal_length_exception": {"id": FRANCISCA, "sha256": FRANCISCA_SHA, "words": 114},
        "previous_metadata_preserved": True, "training_performed": False,
        "predictions_performed": False, "new_metrics": False, "production_changed": False,
        "limitations": ["AI-assisted annotation, not independent human gold.",
            "Works and quoted documents are not automatically independent sources.",
            "Mixed changes to training do not isolate one cause of any later score difference.",
            "Licenses and unresolved rights remain source-specific; local copy is not publication permission."]}
    inputs.unchanged()
    return updated, archive, report, inputs


def encoded(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory inside outputs/")
    args = parser.parse_args()
    target = output_target(args.output)
    updated, archive, report, inputs = build()
    payloads = {"reviewed-export.json": encoded(updated), "replacement-archive.json": encoded(archive)}
    report["outputs"] = [{"path": (target / name).relative_to(ROOT).as_posix(),
        "file_sha256": sha(data), "bytes": len(data)} for name, data in payloads.items()]
    payloads["build-report.json"] = encoded(report)
    require(json.loads(payloads["reviewed-export.json"]) == updated and
            json.loads(payloads["replacement-archive.json"]) == archive, "Serialization changed values")
    inputs.unchanged()
    output_target(target)
    target.mkdir(parents=True, exist_ok=False)
    for name, data in payloads.items():
        with (target / name).open("xb") as handle:
            handle.write(data)
        require((target / name).read_bytes() == data, "Output byte verification failed")
    inputs.unchanged()
    print(json.dumps({"status": report["status"], "split_counts": report["audit"]["split_counts"],
        "replaced_in_place": 9, "quarantined_rows": 7, "added_rows": 30,
        "report": (target / "build-report.json").relative_to(ROOT).as_posix(),
        "reviewed_file_sha256": sha(payloads["reviewed-export.json"]), "training_performed": False}))


if __name__ == "__main__":
    main()
