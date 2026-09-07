"""Añade HUE01 revisado por IA a una copia local; conserva evaluación y procedencia."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from prepare_agn_pilot import digest, grams, normalize, similarities
from prepare_huerta_pilot import prepare

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/ml"))
from app.ml.experiment_data import fingerprint, validate_snapshot

REVIEW_PATH = ROOT / "artifacts/reviews/huerta-pilot-v1.json"
REFERENCE_PATH = ROOT / "artifacts/datasets/gold-v1-source-aware.json"
REFERENCE_SHA = "dcd8d90081973b7b9a05ee6ef41623756a06232727f3718268945d71a207310a"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def incorporate(base: dict, reference: dict, candidate: dict, review: dict) -> tuple[dict, dict]:
    validate_snapshot(base)
    validate_snapshot(reference)
    holdout = lambda data: [r for r in data["items"] if r["split"] != "train"]
    if base["labels"] != reference["labels"] or holdout(base) != holdout(reference):
        raise ValueError("La taxonomía y la evaluación deben coincidir con la referencia")
    verdict = review["review"]
    label = candidate["proposed_label"]
    if (review["status"] != "thematically_approved_not_applied"
            or candidate["candidate_id"] != "HUE01" or review["candidate_id"] != "HUE01"
            or verdict["decision"] != "aprobar_etiqueta"
            or verdict["first_reviewer_label"] != label or verdict["second_reviewer_label"] != label
            or label not in base["labels"]
            or candidate["assigned_split"] is not None or candidate["dataset_applied"]):
        raise ValueError("Se requiere el candidato HUE01 y su acuerdo temático registrado")
    # El manifiesto omite textos completos; los campos compartidos deben coincidir.
    shared = candidate.keys() & review.keys() - {"context_pages"}
    context = [{k: v for k, v in page.items() if k != "text"} for page in candidate["context_pages"]]
    if context != review["context_pages"] or any(candidate[key] != review[key] for key in shared):
        raise ValueError("El candidato no coincide con el manifiesto revisado")
    if digest(candidate["text"].encode()) != verdict["exact_text_sha256"]:
        raise ValueError("El texto cambió después de la revisión")
    source_id = str(uuid5(NAMESPACE_URL, "https://doi.org/" + candidate["source"]["doi"]))
    metadata = base["dataset"]
    if (source_id in {r["resourceId"] for r in base["items"]}
            or source_id in metadata.get("source_registry", {})
            or any(p.get("related_document_group") == candidate["document_group"]
                   or p.get("candidate_id") == "HUE01"
                   for p in metadata.get("added_rows_provenance", []))):
        raise ValueError("La fuente o el documento ya está incorporado; revisar su agrupación")
    candidate_grams = grams(candidate["text"])
    for row in base["items"]:
        j, c = similarities(candidate_grams, grams(row["text"]))
        if normalize(row["text"]) == normalize(candidate["text"]) or j >= 0.25 or c >= 0.8:
            raise ValueError("Hay un solapamiento que requiere revisión antes de incorporar")
    updated = copy.deepcopy(base)
    updated["items"].append({"text": candidate["text"], "label": label,
                             "resourceId": source_id, "sourceType": "pdf", "split": "train"})
    provenance = {
        "candidate_id": "HUE01", "resource_id": source_id,
        "text_sha256": candidate["text_sha256"], "label": label,
        "pdf_page": candidate["pdf_page"], "printed_page": candidate["printed_page"],
        "source_group": candidate["source_group"], "related_document_group": candidate["document_group"],
        "archival_reference": copy.deepcopy(candidate["archival_reference"]),
        "quality_flags": copy.deepcopy(candidate["quality_flags"]),
        "normalization": candidate["normalization"], "extraction_changes": candidate["extraction_changes"],
        "local_context": copy.deepcopy(review["local_candidate"]),
        "review_path": REVIEW_PATH.relative_to(ROOT).as_posix(), "review_sha256": fingerprint(review),
        "annotation_origin": "two_ai_reviews_nonblind", "human_expert_validation": False,
    }
    metadata = updated["dataset"]
    metadata.update({"id": str(uuid5(NAMESPACE_URL, fingerprint(base) + ":huerta:" + fingerprint(review))),
                     "name": "Experimental: revisión histórica y piloto Huerta v1",
                     "status": "experimental_local", "parent_sha256": fingerprint(base)})
    source = copy.deepcopy(candidate["source"])
    source.update({"assigned_split": "train", "changes_notice": candidate["normalization"]})
    metadata.setdefault("source_registry", {})[source_id] = source
    metadata.setdefault("added_rows_provenance", []).append(provenance)
    if updated["items"][:-1] != base["items"] or holdout(updated) != holdout(reference):
        raise ValueError("Las filas anteriores y la evaluación deben permanecer idénticas")
    audit = validate_snapshot(updated)
    report = {"status": "experimental_local", "parent_sha256": fingerprint(base),
              "reference_sha256": fingerprint(reference), "reviewed_sha256": fingerprint(updated),
              "evaluation_sha256": fingerprint(holdout(updated)), "audit": audit,
              "parent_rows_preserved": len(base["items"]), "added": 1, "removed": 0, "relabeled": 0,
              "provenance": provenance, "training_performed": False, "production_changed": False}
    return updated, report


def build() -> tuple[dict, dict]:
    review = read(REVIEW_PATH)
    entries = {**review["inputs"], "candidate": review["local_candidate"], "builder": review["builder"],
               "reference": {"path": REFERENCE_PATH.relative_to(ROOT).as_posix(),
                             "file_sha256": REFERENCE_SHA}}
    for entry in entries.values():
        if digest((ROOT / entry["path"]).read_bytes()) != entry["file_sha256"]:
            raise ValueError(f"Entrada alterada: {entry['path']}")
    candidate = read(ROOT / entries["candidate"]["path"])
    if prepare() != candidate:
        raise ValueError("El candidato no coincide con su extracción reproducible")
    base_path = ROOT / entries["dataset"]["path"]
    updated, report = incorporate(read(base_path), read(REFERENCE_PATH), candidate, review)
    report["inputs"] = {**entries, "review": {"path": REVIEW_PATH.relative_to(ROOT).as_posix(),
                                              "file_sha256": digest(REVIEW_PATH.read_bytes())}}
    report["parent_context_directory"] = base_path.parent.relative_to(ROOT).as_posix()
    # El archivo de Fonseca pertenece a una versión anterior: conservar su ubicación explícita.
    archive = ROOT / "outputs/fonseca-snapshot-v1/replacement-archive.json"
    report["prior_context_archives"] = [{"path": archive.relative_to(ROOT).as_posix(),
                                        "file_sha256": digest(archive.read_bytes())}]
    return updated, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Carpeta nueva dentro de outputs/")
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa una carpeta nueva dentro de outputs/; no se sobrescriben resultados")
    updated, report = build()
    target.mkdir(parents=True, exist_ok=False)
    for name, payload in (("reviewed-export.json", updated), ("build-report.json", report)):
        with (target / name).open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"added": 1, "split_counts": report["audit"]["split_counts"],
                      "training_performed": False}))


if __name__ == "__main__":
    main()
