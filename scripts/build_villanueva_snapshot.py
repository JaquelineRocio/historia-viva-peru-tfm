"""Incorpora la reparación revisada de Villanueva en otra copia local."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from prepare_agn_pilot import digest, grams, normalize, similarities
from prepare_villanueva_repair import prepare

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/ml"))
from app.ml.experiment_data import fingerprint, validate_snapshot

REVIEW_PATH = ROOT / "artifacts/reviews/villanueva-repair-v1.json"
REVIEW_SHA = "93a16704a5e777a0d557e3553cd49451b82ba884abb8b2b1374213b207e859e9"
PARENT_EVIDENCE = ROOT / "artifacts/reviews/huerta-batch-snapshot-v1.json"
PARENT_SHA = "46dd97c12ef8089e359f3270f369179db73e3a373163ab60502a0e06b86731bc"
REMOVED = [7, 633, 15, 14, 10, 637]
CANDIDATES = ["V03", "V04", "V06", "V07"]
CONTEXT = ["V01", "V02", "V05", "V08"]


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def incorporate(base: dict, reference: dict, proposal: dict, review: dict) -> tuple[dict, dict, dict]:
    validate_snapshot(base)
    validate_snapshot(reference)
    holdout = lambda data: [r for r in data["items"] if r["split"] != "train"]
    if base["labels"] != reference["labels"] or holdout(base) != holdout(reference):
        raise ValueError("La taxonomía y la evaluación deben conservarse")
    if (review["status"] != "reviewed_repair_proposal_not_applied" or review["dataset_applied"]
            or proposal["dataset_applied"] or proposal["remove_indices"] != REMOVED
            or proposal["source_id"] != review["source_id"] or proposal["source"] != review["source"]):
        raise ValueError("No coincide la propuesta de sustitución revisada")
    source_id = review["source_id"]
    if (len(proposal["units"]) != 8 or len(review["units"]) != 8
            or [u["id"] for u in proposal["units"]] != [u["id"] for u in review["units"]]):
        raise ValueError("Deben conservarse las ocho unidades revisadas")
    candidates, contexts = [], []
    for unit, verdict in zip(proposal["units"], review["units"]):
        if any(unit[k] != verdict[k] for k in unit if k not in ("text", "raw_text")):
            raise ValueError("Texto, etiqueta o procedencia distintos de la revisión")
        if (digest(unit["text"].encode()) != unit["text_sha256"]
                or digest(unit["raw_text"].encode()) != unit["raw_text_sha256"] or unit["dataset_applied"]):
            raise ValueError("Texto alterado o unidad ya aplicada")
        if unit["disposition"] == "candidate":
            if (verdict["decision"] != "candidate_after_joint_review"
                    or unit["proposed_label"] not in base["labels"]
                    or not 120 <= len(unit["text"].split()) <= 250):
                raise ValueError("Candidato sin dictamen o longitud válida")
            candidates.append(unit)
        else:
            if unit["proposed_label"] is not None:
                raise ValueError("El contexto no debe tener etiqueta de entrenamiento")
            contexts.append(unit)
    if [u["id"] for u in candidates] != CANDIDATES or [u["id"] for u in contexts] != CONTEXT:
        raise ValueError("Cambió el conjunto de candidatos o contextos")
    if ([a["index"] for a in proposal["original_archive"]] != REMOVED
            or [a["index"] for a in review["proposed_removal"]] != REMOVED):
        raise ValueError("Deben archivarse exactamente las seis filas acordadas")
    for archived, target in zip(proposal["original_archive"], review["proposed_removal"]):
        index = target["index"]
        row = base["items"][index]
        parts = [{k: v for k, v in p.items() if k != "text"} for p in archived["partitions"]]
        if (row != archived["row"] or row["split"] != "train" or row["resourceId"] != source_id
                or row["label"] != target["label"] or digest(row["text"].encode()) != target["text_sha256"]
                or parts != target["partitions"] or "".join(p["text"] for p in archived["partitions"]) != row["text"]):
            raise ValueError("Original alterado, fuera de train o archivo incompleto")
    updated = copy.deepcopy(base)
    remaining = [row for i, row in enumerate(base["items"]) if i not in REMOVED]
    updated["items"] = copy.deepcopy(remaining)
    for unit in candidates:
        for row in updated["items"]:
            j, c = similarities(grams(unit["text"]), grams(row["text"]))
            if normalize(unit["text"]) == normalize(row["text"]) or j >= .25 or c >= .8:
                raise ValueError("Solapamiento pendiente fuera de las filas sustituidas")
        updated["items"].append(dict(text=unit["text"], label=unit["proposed_label"],
                                    resourceId=source_id, sourceType="pdf", split="train"))
    archive = copy.deepcopy(proposal)
    archive.update(status="archived_for_local_replacement", review_file_sha256=REVIEW_SHA,
                   parent_sha256=fingerprint(base), context_ids=CONTEXT,
                   warning="Originales y contexto conservados; este archivo no es un dataset de entrenamiento.")
    metadata = updated["dataset"]
    metadata.update(id=str(uuid5(NAMESPACE_URL, fingerprint(base) + ":villanueva:" + REVIEW_SHA)),
                    name="Experimental: revisión histórica y reparación Villanueva v1",
                    status="experimental_local", parent_sha256=fingerprint(base))
    registry = metadata.setdefault("source_registry", {})
    registry.setdefault(source_id, {**copy.deepcopy(review["source"]), "assigned_split": "train",
                                    "source_group": source_id})
    provenance = metadata.setdefault("added_rows_provenance", [])
    for unit in candidates:
        identifier = "VIL-" + unit["id"] + "-v1"
        if any(p["candidate_id"] == identifier for p in provenance):
            raise ValueError("El candidato ya tiene una incorporación registrada")
        verdict = next(u for u in review["units"] if u["id"] == unit["id"])
        provenance.append(dict(candidate_id=identifier, resource_id=source_id, source_group=source_id,
                               text_sha256=unit["text_sha256"], label=unit["proposed_label"],
                               parts=copy.deepcopy(unit["parts"]), extraction_changes=copy.deepcopy(unit["changes"]),
                               quality_flags=copy.deepcopy(verdict["quality_flags"]),
                               related_context_ids=["V02"] if unit["id"] == "V03" else [],
                               replaced_parent_indices=REMOVED.copy(), review_path=REVIEW_PATH.relative_to(ROOT).as_posix(),
                               review_file_sha256=REVIEW_SHA, annotation_origin="two_ai_reviews_nonblind",
                               human_expert_validation=False))
    metadata.setdefault("replacement_history", []).append(dict(
        plan=REVIEW_PATH.relative_to(ROOT).as_posix(), plan_file_sha256=REVIEW_SHA,
        parent_sha256=fingerprint(base), removed_parent_indices=REMOVED.copy(), removed_rows=6, added_rows=4,
        archive="replacement-archive.json", archive_sha256=fingerprint(archive), context_ids=CONTEXT.copy(),
        coverage_reduced_in_training=True, ambiguous_context_ids=["V02"]))
    if updated["items"][:-4] != remaining or holdout(updated) != holdout(reference):
        raise ValueError("Cambió una fila ajena a la sustitución o la evaluación")
    audit = validate_snapshot(updated)
    if len(base["items"]) != 818 or audit["split_counts"] != {"train": 598, "val": 81, "test": 137}:
        raise ValueError("Recuentos distintos de la sustitución prevista")
    report = dict(status="experimental_local", parent_sha256=fingerprint(base),
                  reference_sha256=fingerprint(reference), reviewed_sha256=fingerprint(updated),
                  evaluation_sha256=fingerprint(holdout(updated)), archive_sha256=fingerprint(archive),
                  removed=6, added=4, remaining_rows_preserved=len(remaining), context_ids=CONTEXT.copy(),
                  ambiguous_context_ids=["V02"], new_sources=0, audit=audit,
                  training_performed=False, production_changed=False, new_metrics=False)
    return updated, archive, report


def build() -> tuple[dict, dict, dict]:
    if digest(REVIEW_PATH.read_bytes()) != REVIEW_SHA or digest(PARENT_EVIDENCE.read_bytes()) != PARENT_SHA:
        raise ValueError("Cambió la revisión o evidencia del padre")
    review = read(REVIEW_PATH)
    parent = read(PARENT_EVIDENCE)
    entries = review["inputs"] + [review["boundary_manifest"], review["builder"], review["local_archive"],
                                 dict(path=review["builder"]["helper_path"], file_sha256=review["builder"]["helper_sha256"])]
    entries += parent["prior_context_archives"]
    for entry in entries:
        if digest((ROOT / entry["path"]).read_bytes()) != entry["file_sha256"]:
            raise ValueError(f"Entrada alterada: {entry['path']}")
    proposal = read(ROOT / review["local_archive"]["path"])
    if prepare() != proposal:
        raise ValueError("La extracción ya no reproduce la propuesta revisada")
    base = read(ROOT / review["inputs"][0]["path"])
    reference = read(ROOT / review["inputs"][2]["path"])
    if fingerprint(base) != parent["reviewed_sha256"]:
        raise ValueError("El dataset no coincide con la evidencia del padre")
    updated, archive, report = incorporate(base, reference, proposal, review)
    report.update(inputs=review["inputs"], review_path=REVIEW_PATH.relative_to(ROOT).as_posix(),
                  review_file_sha256=REVIEW_SHA, prior_context_archives=parent["prior_context_archives"],
                  parent_evidence=dict(path=PARENT_EVIDENCE.relative_to(ROOT).as_posix(), file_sha256=PARENT_SHA))
    return updated, archive, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Carpeta nueva dentro de outputs/")
    target = parser.parse_args().output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa una carpeta nueva dentro de outputs/; no se sobrescribe")
    updated, archive, report = build()
    target.mkdir(parents=True, exist_ok=False)
    for name, payload in [("reviewed-export.json", updated), ("replacement-archive.json", archive), ("build-report.json", report)]:
        with (target / name).open("x", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
    print(json.dumps({"split_counts": report["audit"]["split_counts"], "removed": 6, "added": 4,
                      "training_performed": False}))


if __name__ == "__main__":
    main()
