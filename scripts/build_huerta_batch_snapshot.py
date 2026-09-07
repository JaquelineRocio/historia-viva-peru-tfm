"""Incorpora HUE02/03/04 a una copia local con la fuente y evaluación existentes."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from build_huerta_snapshot import ROOT, REFERENCE_PATH, REFERENCE_SHA, read
from app.ml.experiment_data import fingerprint, validate_snapshot
from prepare_agn_pilot import digest, grams, normalize, similarities
from prepare_huerta_batch import prepare

REVIEW_PATH = ROOT / "artifacts/reviews/huerta-batch-v1.json"
PARENT_EVIDENCE = ROOT / "artifacts/reviews/huerta-snapshot-v1.json"
PARENT_EVIDENCE_SHA = "9f8571f0642d4b9fd993929fa192ea149da817e1941a478a3a8702c4f36b7e71"
IDENTIFIERS = ["HUE02", "HUE03", "HUE04"]


def incorporate(base: dict, reference: dict, batch: dict, review: dict) -> tuple[dict, dict]:
    validate_snapshot(base)
    validate_snapshot(reference)
    holdout = lambda data: [r for r in data["items"] if r["split"] != "train"]
    if base["labels"] != reference["labels"] or holdout(base) != holdout(reference):
        raise ValueError("La taxonomía y la evaluación deben coincidir con la referencia")
    if (review["status"] != "three_candidates_reviewed_not_applied" or review["dataset_applied"]
            or review["source_split"] != "train" or batch["source_split"] != "train"
            or [r["id"] for r in batch["items"]] != IDENTIFIERS
            or [r["id"] for r in review["items"]] != IDENTIFIERS
            or batch["source"] != review["source"]):
        raise ValueError("Se requiere el lote completo revisado HUE02/03/04 en train")
    context = [{k: v for k, v in p.items() if k != "text"} for p in batch["context_pages"]]
    if context != review["context_pages"]:
        raise ValueError("El contexto no coincide con la revisión")
    source_id = str(uuid5(NAMESPACE_URL, "https://doi.org/" + review["source"]["doi"]))
    source_group = review["source"]["source_group"]
    registry = base["dataset"]["source_registry"].get(source_id, {})
    source_rows = [r for r in base["items"] if r["resourceId"] == source_id]
    if (registry.get("source_group") != source_group or registry.get("assigned_split") != "train"
            or not source_rows or any(r["split"] != "train" for r in source_rows)):
        raise ValueError("La fuente de Huerta debe existir exclusivamente en entrenamiento")
    updated = copy.deepcopy(base)
    existing = updated["dataset"]["added_rows_provenance"]
    provenance = []
    for candidate, item in zip(batch["items"], review["items"]):
        verdict, label = item["review"], item["proposed_label"]
        shared = candidate.keys() & item.keys() - {"annotation_status"}
        if (any(candidate[k] != item[k] for k in shared)
                or item["annotation_status"] != "thematically_approved_not_applied"
                or verdict["decision"] != "aprobar_etiqueta"
                or verdict["training_selection"] != "candidate_for_future_training"
                or verdict["first_reviewer_label"] != label or verdict["second_reviewer_label"] != label
                or label not in base["labels"] or item["dataset_applied"]
                or item["source_split"] != "train" or item["source_group"] != source_group
                or digest(candidate["text"].encode()) != verdict["exact_text_sha256"]
                or candidate["text_sha256"] != verdict["exact_text_sha256"]):
            raise ValueError("Texto, fuente o dictamen distintos del candidato aprobado")
        if any(p["candidate_id"] == item["id"] or p.get("related_document_group") == item["document_group"]
               for p in existing):
            raise ValueError("El candidato o grupo documental ya se incorporó")
        if any(identifier not in IDENTIFIERS for identifier in item["related_candidate_ids"]):
            raise ValueError("Falta un candidato relacionado del lote revisado")
        for row in updated["items"]:
            j, c = similarities(grams(candidate["text"]), grams(row["text"]))
            if normalize(candidate["text"]) == normalize(row["text"]) or j >= .25 or c >= .8:
                raise ValueError("Hay un solapamiento que requiere revisión")
        updated["items"].append({"text": candidate["text"], "label": label,
                                 "resourceId": source_id, "sourceType": "pdf", "split": "train"})
        entry = {"candidate_id": item["id"], "resource_id": source_id, "label": label,
                 "source_group": source_group, "related_document_group": item["document_group"],
                 **{k: copy.deepcopy(item[k]) for k in (
                     "text_sha256", "pdf_page", "printed_page", "direct_reference", "quality_flags",
                     "conditions", "related_candidate_ids", "extraction_changes", "confidence")},
                 "annotation_origin": "two_ai_reviews_nonblind", "human_expert_validation": False,
                 "local_context": copy.deepcopy(review["local_candidates"]),
                 "review_path": REVIEW_PATH.relative_to(ROOT).as_posix(), "review_sha256": fingerprint(review)}
        if item["id"] == "HUE02":
            entry["quotation_start_marker"] = "Por tanto, ciudadanos,"
        existing.append(entry)
        provenance.append(entry)
    updated["dataset"].update({
        "id": str(uuid5(NAMESPACE_URL, fingerprint(base) + ":huerta-batch:" + fingerprint(review))),
        "name": "Experimental: revisión histórica y cuatro pasajes de Huerta",
        "status": "experimental_local", "parent_sha256": fingerprint(base)})
    if updated["items"][:-3] != base["items"] or holdout(updated) != holdout(reference):
        raise ValueError("Las filas anteriores y la evaluación deben permanecer idénticas")
    report = {"status": "experimental_local", "parent_sha256": fingerprint(base),
              "reference_sha256": fingerprint(reference), "reviewed_sha256": fingerprint(updated),
              "evaluation_sha256": fingerprint(holdout(updated)), "audit": validate_snapshot(updated),
              "parent_rows_preserved": len(base["items"]), "added": 3, "removed": 0, "relabeled": 0,
              "new_sources": 0, "provenance": provenance,
              "training_performed": False, "production_changed": False}
    return updated, report


def build() -> tuple[dict, dict]:
    review = read(REVIEW_PATH)
    entries = {**review["inputs"], "candidates": review["local_candidates"], "builder": review["builder"],
               "reference": {"path": REFERENCE_PATH.relative_to(ROOT).as_posix(), "file_sha256": REFERENCE_SHA},
               "parent_evidence": {"path": PARENT_EVIDENCE.relative_to(ROOT).as_posix(),
                                   "file_sha256": PARENT_EVIDENCE_SHA}}
    for entry in entries.values():
        if digest((ROOT / entry["path"]).read_bytes()) != entry["file_sha256"]:
            raise ValueError(f"Entrada alterada: {entry['path']}")
    batch = read(ROOT / entries["candidates"]["path"])
    if json.loads(json.dumps(prepare())) != batch:
        raise ValueError("El lote no coincide con su extracción reproducible")
    updated, report = incorporate(read(ROOT / entries["dataset"]["path"]), read(REFERENCE_PATH), batch, review)
    archives = read(PARENT_EVIDENCE)["prior_context_archives"]
    for entry in archives:
        if digest((ROOT / entry["path"]).read_bytes()) != entry["file_sha256"]:
            raise ValueError("El archivo de contexto anterior cambió")
    report.update({"inputs": {**entries, "review": {"path": REVIEW_PATH.relative_to(ROOT).as_posix(),
                                                    "file_sha256": digest(REVIEW_PATH.read_bytes())}},
                   "parent_context_directory": Path(entries["dataset"]["path"]).parent.as_posix(),
                   "prior_context_archives": archives})
    return updated, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Carpeta nueva dentro de outputs/")
    target = parser.parse_args().output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa una carpeta nueva dentro de outputs/; no se sobrescriben resultados")
    updated, report = build()
    target.mkdir(parents=True, exist_ok=False)
    for name, payload in (("reviewed-export.json", updated), ("build-report.json", report)):
        with (target / name).open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"added": 3, "split_counts": report["audit"]["split_counts"],
                      "training_performed": False}))


if __name__ == "__main__":
    main()
