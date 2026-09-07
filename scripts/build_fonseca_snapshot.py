"""Aplica la sustitución revisada de Fonseca en una copia local y archiva originales."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from pypdf import PdfReader

from prepare_fonseca_repair import prepare
from prepare_agn_pilot import digest, grams, normalize, similarities

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/ml"))
from app.ml.experiment_data import fingerprint, validate_snapshot

PLAN_PATH = ROOT / "artifacts/reviews/fonseca-replacement-v1.json"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> tuple[dict, dict, dict]:
    plan = read(PLAN_PATH)
    if plan["status"] != "approved_for_local_experimental_replacement":
        raise ValueError("La sustitución no está aprobada para la copia experimental")
    for entry in plan["inputs"].values():
        if digest((ROOT / entry["path"]).read_bytes()) != entry["file_sha256"]:
            raise ValueError(f"Entrada de sustitución alterada: {entry['path']}")
    base = read(ROOT / plan["inputs"]["base"]["path"])
    candidate = read(ROOT / plan["inputs"]["candidate"]["path"])
    if prepare() != candidate:
        raise ValueError("El candidato no coincide con su extracción reproducible")
    validate_snapshot(base)
    operation = plan["operation"]
    source_id = operation["source_id"]
    label = operation["replacement_label"]
    if (operation["split"] != "train" or candidate["source_id"] != source_id
            or candidate["proposed_label"] != label or label not in base["labels"]
            or operation["replacement_candidate"] != candidate["candidate_id"]):
        raise ValueError("Fuente, partición o etiqueta no coinciden con el dictamen")
    removed = {}
    for target in operation["remove"]:
        index = target["item_index"]
        if not isinstance(index, int) or not 0 <= index < len(base["items"]) or index in removed:
            raise ValueError("Índice de sustitución inválido o repetido")
        row = base["items"][index]
        if (row["split"] != "train" or row["resourceId"] != source_id
                or row["label"] != target["label"]
                or digest(row["text"].encode()) != target["text_sha256"]):
            raise ValueError("La fila que se pretende sustituir cambió o no pertenece a train")
        removed[index] = copy.deepcopy(row)
    if list(removed) != [55, 57, 58]:
        raise ValueError("Esta versión solo resuelve conjuntamente train55/57/58")
    updated = copy.deepcopy(base)
    remaining = [row for i, row in enumerate(base["items"]) if i not in removed]
    new_row = {"text": candidate["text"], "label": label,
               "resourceId": source_id, "sourceType": "pdf", "split": "train"}
    candidate_grams = grams(new_row["text"])
    for row in remaining:
        j, c = similarities(candidate_grams, grams(row["text"]))
        if normalize(row["text"]) == normalize(new_row["text"]) or j >= 0.25 or c >= 0.8:
            raise ValueError("Persiste un solapamiento marcado fuera del grupo sustituido")
    updated["items"] = copy.deepcopy(remaining) + [new_row]
    holdout = lambda data: [r for r in data["items"] if r["split"] != "train"]
    if holdout(updated) != holdout(base):
        raise ValueError("La evaluación debe permanecer idéntica")
    plan_sha = digest(PLAN_PATH.read_bytes())
    metadata = updated["dataset"]
    metadata.update({"id": str(uuid5(NAMESPACE_URL, fingerprint(base) + ":" + plan_sha)),
                     "name": "Experimental AGN y reparación Fonseca v1",
                     "status": "experimental_local", "parent_sha256": fingerprint(base)})
    metadata.setdefault("source_registry", {})[source_id] = copy.deepcopy(candidate["source"])
    metadata.setdefault("added_rows_provenance", []).append({
        "candidate_id": candidate["candidate_id"], "resource_id": source_id,
        "text_sha256": candidate["text_sha256"], "label": label,
        "pdf_pages": [4, 5], "printed_pages": [108, 109],
        "replaced_parent_indices": list(removed), "replacement_plan_file_sha256": plan_sha,
        "annotation_origin": "two_ai_reviews_with_discussion", "human_expert_validation": False,
    })
    metadata.setdefault("replacement_history", []).append({
        "plan": str(PLAN_PATH.relative_to(ROOT)), "plan_file_sha256": plan_sha,
        "parent_sha256": fingerprint(base), "removed_rows": len(removed), "added_rows": 1,
        "archive": plan["context_archive"]["file_name"], "coverage_reduced_in_training": True,
    })
    audit = validate_snapshot(updated)
    expected = plan["expected_result"]
    if (len(base["items"]) != expected["base_rows"]
            or len(updated["items"]) != expected["total_rows"]
            or audit["split_counts"] != expected["split_counts"]):
        raise ValueError("El recuento no coincide con la sustitución revisada")
    pdf = PdfReader(ROOT / candidate["inputs"]["fonseca"]["path"])
    archive = {
        "status": "context_only_not_training", "plan_file_sha256": plan_sha,
        "parent_sha256": fingerprint(base),
        "original_rows": [{"parent_index": i, "row": row} for i, row in removed.items()],
        "pdf_sha256": candidate["inputs"]["fonseca"]["file_sha256"],
        "pdf_pages": [{"pdf_page": i, "printed_page": i + 104,
                       "text": pdf.pages[i - 1].extract_text(),
                       "layout_text": pdf.pages[i - 1].extract_text(extraction_mode="layout")}
                      for i in plan["context_archive"]["pdf_pages"]],
        "context_notes": plan["context_archive"]["retained_contexts"],
        "warning": "Contexto archivado, no ejemplos nuevos; tabla sin cotejo visual renderizado.",
    }
    report = {"status": "experimental_local", "plan_file_sha256": plan_sha,
              "parent_sha256": fingerprint(base), "reviewed_sha256": fingerprint(updated),
              "archive_sha256": fingerprint(archive), "evaluation_sha256": fingerprint(holdout(updated)),
              "removed_rows": len(removed), "added_rows": 1, "remaining_rows_preserved": len(remaining),
              "audit": audit, "high_overlap_outside_replaced_group": False,
              "coverage_reduced_in_training": True, "training_performed": False,
              "production_changed": False}
    return updated, archive, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Carpeta nueva dentro de outputs/")
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa una carpeta nueva dentro de outputs/; no se sobrescriben resultados")
    updated, archive, report = build()
    target.mkdir(parents=True, exist_ok=False)
    for name, payload in (("reviewed-export.json", updated),
                          ("replacement-archive.json", archive), ("build-report.json", report)):
        with (target / name).open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "split_counts": report["audit"]["split_counts"]}))


if __name__ == "__main__":
    main()
