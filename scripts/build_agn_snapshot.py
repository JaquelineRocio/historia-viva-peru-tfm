"""Export completo experimental: referencia intacta más AGN01/02 revisados por IA."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "ml"))
from app.ml.experiment_data import fingerprint, validate_snapshot

PEER_PATH = ROOT / "artifacts/reviews/agn-pilot-v1-peer-review.json"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> tuple[dict, dict]:
    peer = json.loads(PEER_PATH.read_text(encoding="utf-8"))
    for entry in peer["inputs"].values():
        if file_hash(ROOT / entry["path"]) != entry["file_sha256"]:
            raise ValueError(f"La entrada revisada cambió: {entry['path']}")
    chosen = peer["result"]["proposed_training_candidates"]
    if chosen != ["AGN01", "AGN02"] or peer["result"]["context_only"] != ["AGN03"]:
        raise ValueError("La selección no coincide con el piloto aprobado por ambos revisores IA")
    read = lambda key: json.loads((ROOT / peer["inputs"][key]["path"]).read_text(encoding="utf-8"))
    reference, pilot, first = read("dataset"), read("local_texts"), read("first_review")
    validate_snapshot(reference)
    texts = {row["id"]: row for row in pilot["items"]}
    reviews = {row["id"]: row for row in peer["items"]}
    source = first["source"]
    source_id = str(uuid5(NAMESPACE_URL, "https://doi.org/" + source["doi"]))
    if source_id in {row["resourceId"] for row in reference["items"]}:
        raise ValueError("La fuente ya existe en la referencia; revisar la incorporación")
    reviewed = copy.deepcopy(reference)
    provenance = []
    for identifier in chosen:
        candidate, review = texts[identifier], reviews[identifier]
        if (not review["ai_label_consensus"]
                or review["training_selection"] != "candidate_for_future_training"
                or review["second_reviewer_initial_label"] != review["second_reviewer_final_label"]
                or review["second_reviewer_final_label"] != candidate["proposed_label"]):
            raise ValueError("No hay consenso temático válido para el candidato")
        text = candidate["text"]
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != review["text_sha256"]:
            raise ValueError("El texto no coincide con la segunda revisión")
        reviewed["items"].append({"text": text, "label": review["second_reviewer_final_label"],
                                  "resourceId": source_id, "sourceType": "pdf", "split": "train"})
        provenance.append({"candidate_id": identifier, "resource_id": source_id,
                           "text_sha256": review["text_sha256"], "label": review["second_reviewer_final_label"],
                           "printed_page": candidate["printed_page"], "pdf_page": candidate["pdf_page"],
                           "related_document_group": candidate["related_document_group"],
                           "annotation_origin": "two_ai_reviews", "human_expert_validation": False})
    holdout = lambda data: [r for r in data["items"] if r["split"] != "train"]
    if holdout(reviewed) != holdout(reference) or reviewed["items"][:-2] != reference["items"]:
        raise ValueError("La referencia o sus conjuntos de evaluación fueron modificados")
    reviewed["dataset"] = {
        "id": str(uuid5(NAMESPACE_URL, fingerprint(reference) + ":agn:" + file_hash(PEER_PATH))),
        "name": "Experimental AGN v1: referencia congelada más dos revisiones IA",
        "status": "experimental_local", "reference_sha256": fingerprint(reference),
        "evaluation_sha256": fingerprint(holdout(reference)),
        "new_annotations": "two_ai_reviews_not_independent_human_gold",
        "source_registry": {source_id: {k: source[k] for k in (
            "author", "title", "year", "journal", "volume_issue", "pages", "doi", "url",
            "license", "license_url", "license_evidence", "changes_notice")}},
        "added_rows_provenance": provenance,
    }
    audit = validate_snapshot(reviewed)
    report = {
        "status": "experimental_local", "reference_sha256": fingerprint(reference),
        "peer_review_file_sha256": file_hash(PEER_PATH),
        "reviewed_sha256": fingerprint(reviewed), "evaluation_sha256": fingerprint(holdout(reviewed)),
        "reference_rows_preserved": len(reference["items"]), "added": 2, "removed": 0, "relabeled": 0,
        "excluded_from_new_rows": ["AGN03"], "new_source_id": source_id,
        "audit": audit, "provenance": provenance, "production_changed": False,
        "warning": "Export experimental local; no implica entrenamiento ni gold validado por historiadores.",
    }
    return reviewed, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Carpeta local nueva en outputs/")
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa una carpeta nueva dentro de outputs/; no se sobrescriben resultados")
    reviewed, report = build()
    target.mkdir(parents=True, exist_ok=False)
    for name, payload in (("reviewed-export.json", reviewed), ("build-report.json", report)):
        with (target / name).open("x", encoding="utf-8") as output:
            output.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "added": report["added"],
                      "split_counts": report["audit"]["split_counts"]}))


if __name__ == "__main__":
    main()
