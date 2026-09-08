"""Aplica solo las reparaciones históricas v2 en una copia experimental nueva."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from prepare_agn_pilot import digest, grams, normalize, similarities

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/ml"))
from app.ml.experiment_data import fingerprint, validate_snapshot

REVIEW = "artifacts/reviews/corpus-closure-v2.json"
REVIEW_SHA = "9f8bee3c7070fd7ec190abd51b8c843d426e6f64b5204d179a60259acab23875"
PARENT_REPORT = "artifacts/reviews/villanueva-snapshot-v1.json"
PARENT_REPORT_SHA = "e1695bf84f9c25a727d8047dfe5694665eddee08da55e872c778f9c73a9664f6"
REFERENCE = "artifacts/datasets/gold-v1-source-aware.json"
REFERENCE_SHA = "dcd8d90081973b7b9a05ee6ef41623756a06232727f3718268945d71a207310a"
PROPOSAL = "outputs/corpus-closure-v2/consolidated-local.json"
OPERATIONS = {19: "ORR-F2-context", 24: "ORR-F2", 25: None,
              78: "FON-D1", 149: None, 157: "FON-R157", 162: "FON-R162",
              598: "OPH-R1", 608: "OPH-A1"}
SHORT_ID = "ORR-F2-context"
SHORT_SHA = "a1fa148c95732256b62a29668f731ee785d5d22aab9f95cbe17df7126dfaf66b"
CONTEXT_PATHS = ["outputs/corpus-closure-v2/opheland/context.json",
                 "outputs/corpus-closure-v2/opheland/proposal.json",
                 "outputs/corpus-closure-v2/orrego/proposal-v2.json",
                 "outputs/corpus-closure-v2/fonseca/proposal-v2.json"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def checked_json(path: str, expected_sha: str) -> dict:
    data = (ROOT / path).read_bytes()
    require(digest(data) == expected_sha, f"Entrada alterada: {path}")
    return json.loads(data)


def holdout(data: dict) -> list:
    return [r for r in data["items"] if r["split"] != "train"]


def incorporate(base: dict, reference: dict, proposal: dict, review: dict,
                source_contexts: list, prior_archives: list) -> tuple[dict, dict, dict]:
    """Transformación sin escritura. Todas las comprobaciones preceden al export."""
    validate_snapshot(base)
    validate_snapshot(reference)
    require(base["labels"] == reference["labels"] and holdout(base) == holdout(reference),
            "Taxonomía o evaluación distintas de la referencia")
    require(not review["dataset_applied"] and not proposal["applied"] and
            review["status"] == "reviewed_local_proposal_not_applied", "Revisión incompatible")
    require(proposal["affected_original_indices"] == list(OPERATIONS), "Cambió el grupo acordado")
    operations = review["operations_repairs_only"]
    require([r["index_base_zero"] for r in operations] == list(OPERATIONS), "Operaciones distintas")
    selected = {c["id"]: c for c in proposal["repair_units"]}
    require(len(selected) == len(proposal["repair_units"]) == 7 and
            set(selected) == set(OPERATIONS.values()) - {None}, "Solo se admiten siete reparaciones")
    verdicts = {c["id"]: c for c in review["units"]}
    originals, spans_count, characters = [], 0, 0
    require([r["index"] for r in proposal["original_partitions"]] ==
            [598, 608, 19, 24, 25, 78, 149, 157, 162], "Archivo de originales distinto")
    for archived in proposal["original_partitions"]:
        index = archived["index"]
        row = base["items"][index]
        require(row["split"] == "train" and digest(row["text"].encode()) == archived["sha256"],
                f"Original alterado o fuera de train: {index}")
        cursor = 0
        for part in archived["parts"]:
            require(part["start"] == cursor and part["end"] > cursor and
                    row["text"][part["start"]:part["end"]] == part["text"] and
                    digest(part["text"].encode()) == part["sha256"], "Partición incompleta o alterada")
            cursor = part["end"]
        require(cursor == len(row["text"]), "Falta contenido original en el archivo")
        originals.append({"parent_index": index, "row": copy.deepcopy(row),
                          "text_sha256": archived["sha256"], "partitions": copy.deepcopy(archived["parts"])})
        spans_count += len(archived["parts"])
        characters += cursor
    require((len(originals), spans_count, characters) == (9, 75, 9312), "Archivo incompleto")
    for op in operations:
        index = op["index_base_zero"]
        row = base["items"][index]
        uid = OPERATIONS[index]
        require(row["label"] == op["original_label"] and row["resourceId"] == op["resource_id"] and
                row["sourceType"] == "pdf" and digest(row["text"].encode()) == op["expected_text_sha256"],
                "Cambió una fila de la operación")
        if uid is None:
            require(op["action"] == "retire_row_after_archiving", "Retiro no acordado")
            continue
        c, v = selected[uid], verdicts[uid]
        require(op["action"] == "replace_text_only" and op["unit_id"] == uid and
                c["replace_index"] == index and c["source_id"] == row["resourceId"] and
                c["label"] == row["label"] == v["label"], "Etiqueta, fuente o posición cambiadas")
        require({k: value for k, value in c.items() if k != "text"} ==
                {k: v[k] for k in c if k != "text"}, "Procedencia distinta del dictamen")
        text_sha = digest(c["text"].encode())
        words = len(c["text"].split())
        require(text_sha == c["text_sha256"] == v["text_sha256"] == op["new_text_sha256"] and
                words == c["word_count"], "Texto candidato alterado")
        if not 120 <= words <= 250:
            require(uid == SHORT_ID and text_sha == SHORT_SHA and words == 109 and
                    v["length_exception"] == {"sha256": SHORT_SHA, "word_count": 109},
                    "Excepción de longitud no autorizada")

    # Comparación mecánica únicamente: no se emiten textos/etiquetas de evaluación.
    remaining = [r for i, r in enumerate(base["items"]) if i not in OPERATIONS]
    references = [(normalize(r["text"]), grams(r["text"])) for r in remaining]
    overlap_comparisons = 0
    for c in selected.values():
        n, g = normalize(c["text"]), grams(c["text"])
        for other, og in references:
            j, containment = similarities(g, og)
            require(n != other and n not in other and other not in n and j < .25 and containment < .8,
                    "Solapamiento pendiente fuera del grupo sustituido")
            overlap_comparisons += 1
        references.append((n, g))

    updated = copy.deepcopy(base)
    new_rows, origin_indices, row_map = [], [], []
    for old_index, row in enumerate(base["items"]):
        if old_index in OPERATIONS and OPERATIONS[old_index] is None:
            row_map.append({"parent_index": old_index, "new_index": None, "action": "retired"})
            continue
        new = copy.deepcopy(row)
        if old_index in OPERATIONS:
            c = selected[OPERATIONS[old_index]]
            new["text"] = c["text"]
            require({k: v for k, v in new.items() if k != "text"} ==
                    {k: v for k, v in row.items() if k != "text"}, "Cambió un campo distinto de text")
            row_map.append({"parent_index": old_index, "new_index": len(new_rows),
                            "action": "text_replaced", "unit_id": c["id"]})
        else:
            require(new == row, "Cambió una fila ajena a la operación")
        new_rows.append(new)
        origin_indices.append(old_index)
    updated["items"] = new_rows
    require([r for i, r in zip(origin_indices, new_rows) if i not in OPERATIONS] == remaining and
            len(remaining) == 807 and holdout(updated) == holdout(reference),
            "Cambió el orden o contenido de filas no afectadas o evaluación")
    require(set(base) == {"dataset", "labels", "items"}, "Estructura del export inesperada")

    # Resolver la procedencia faltante en el resumen, desde el JSON fuente verificado.
    fonseca = next(e for e in source_contexts if e["path"].endswith("fonseca/proposal-v2.json"))["payload"]
    fonseca_units = {u["id"]: u for u in [fonseca["primary_candidate"]] + fonseca["additional_candidates"]}
    provenance = []
    for mapping in row_map:
        if mapping["action"] != "text_replaced":
            continue
        uid = mapping["unit_id"]
        c, v = selected[uid], verdicts[uid]
        locators = copy.deepcopy(c["locators"])
        locator_basis = c["local_proposal"]
        resolved_missing = False
        if uid in fonseca_units:
            source = fonseca_units[uid]
            require(source["text_sha256"] == c["text_sha256"], "Localizador de otra unidad")
            locators = {"printed_pages": source["printed_pages"], "pdf_pages": source["pdf_pages"]}
            resolved_missing = True
        require(bool(locators), "Falta localizador de página")
        provenance.append({"candidate_id": "CORPUS-v2-" + uid, "unit_id": uid,
                           "resource_id": c["source_id"], "text_sha256": c["text_sha256"],
                           "label": c["label"], "parent_index": mapping["parent_index"],
                           "index_in_this_snapshot": mapping["new_index"], "index_base": 0,
                           "locators": locators, "locator_basis": locator_basis,
                           "resolved_missing_consolidated_locator": resolved_missing,
                           "review_path": REVIEW, "review_file_sha256": REVIEW_SHA,
                           "length_exception": copy.deepcopy(v["length_exception"]),
                           "decision": copy.deepcopy(v["decision"]),
                           "annotation_origin": "ai_assisted_nonblind", "human_expert_validation": False})
    archive = {"status": "archived_for_local_corpus_replacement_not_training_data",
               "review_path": REVIEW, "review_file_sha256": REVIEW_SHA,
               "parent_dataset_metadata": copy.deepcopy(base["dataset"]),
               "originals": originals, "candidate_units": copy.deepcopy(list(selected.values())),
               "source_contexts": copy.deepcopy(source_contexts),
               "prior_archives": copy.deepcopy(prior_archives), "row_mapping": row_map,
               "coverage_tradeoffs": copy.deepcopy(review["coverage_tradeoffs"]),
               "review_decisions": copy.deepcopy(review["review_decisions"])}
    metadata = updated["dataset"]
    previous_provenance = copy.deepcopy(metadata["added_rows_provenance"])
    previous_history = copy.deepcopy(metadata["replacement_history"])
    require(not any(p["candidate_id"].startswith("CORPUS-v2-") for p in previous_provenance),
            "La reparación ya tiene procedencia registrada")
    metadata.update(id=str(uuid5(NAMESPACE_URL, fingerprint(base) + ":corpus-repair-v2:" + REVIEW_SHA)),
                    name="Experimental: reparaciones históricas del corpus v2",
                    status="experimental_local", parent_sha256=fingerprint(base))
    metadata["added_rows_provenance"].extend(provenance)
    metadata["replacement_history"].append({"plan": REVIEW, "plan_file_sha256": REVIEW_SHA,
        "parent_sha256": fingerprint(base), "parent_file_sha256": review["input_snapshot"]["sha256"],
        "affected_parent_indices": list(OPERATIONS), "rows_replaced_in_place": 7,
        "retired_parent_indices": [25, 149], "removed_rows": 9, "added_rows": 7,
        "new_sources": 0, "archive": "replacement-archive.json",
        "archive_sha256": fingerprint(archive), "archive_hash_kind": "canonical_json_sha256",
        "coverage_reduced_in_selected_training_rows": True, "retained_context_raw_words": 144})
    metadata["parent_archive_dependencies"] = [
        {"path": e["path"], "file_sha256": e["file_sha256"],
         "canonical_json_sha256": e["canonical_json_sha256"],
         "embedded_in": "replacement-archive.json:prior_archives"} for e in prior_archives]
    require(metadata["added_rows_provenance"][:-7] == previous_provenance and
            metadata["replacement_history"][:-1] == previous_history, "Se alteró el historial previo")
    mutable = {"id", "name", "status", "parent_sha256", "added_rows_provenance", "replacement_history",
               "parent_archive_dependencies"}
    require(all(metadata[k] == value for k, value in base["dataset"].items() if k not in mutable),
            "Se alteró otro metadato previo")
    audit = validate_snapshot(updated)
    require(audit["split_counts"] == {"train": 596, "val": 81, "test": 137} and len(new_rows) == 814,
            "Recuentos distintos de lo acordado")
    require(audit["class_distribution"]["train"] == review["simulation"]["repairs_only"]["train_by_label"] and
            audit["sources_by_split"] == validate_snapshot(base)["sources_by_split"], "Cambió una clase o fuente")
    require(not any(r["resourceId"] == review["append_separate"]["proposed_resource_id"] for r in new_rows),
            "El alta separada no está autorizada en este bloque")
    duplicate_indices = [origin_indices.index(i) for i in (709, 737)]
    require(new_rows[duplicate_indices[0]]["text"] == new_rows[duplicate_indices[1]]["text"],
            "Cambió el duplicado previo fuera del alcance acordado")
    report = {"status": "experimental_local_verified", "review_path": REVIEW, "review_file_sha256": REVIEW_SHA,
              "parent_sha256": fingerprint(base), "reference_sha256": fingerprint(reference),
              "reviewed_sha256": fingerprint(updated), "evaluation_sha256": fingerprint(holdout(updated)),
              "archive_sha256": fingerprint(archive), "hash_kind": "canonical_json_sha256",
              "audit": audit, "affected_rows": 9, "replaced_in_place": 7, "retired_rows": 2,
              "row_mapping": row_map, "unchanged_rows_preserved_in_relative_order": 807,
              "archived_partitions": spans_count, "archived_original_characters": characters,
              "overlap_comparisons": overlap_comparisons, "overlap_alerts": 0,
              "overlap_scope": "Siete candidatos frente a filas restantes y entre candidatos; no auditoría de duplicados de todo train",
              "preexisting_train_duplicate_preserved": {"parent_indices": [709, 737],
                                                         "new_indices": duplicate_indices},
              "new_sources": 0, "separate_addition_included": False,
              "provenance": provenance, "parent_archive_dependencies": metadata["parent_archive_dependencies"],
              "training_performed": False, "new_metrics": False, "production_changed": False}
    return updated, archive, report


def build() -> tuple[dict, dict, dict]:
    review = checked_json(REVIEW, REVIEW_SHA)
    parent = checked_json(PARENT_REPORT, PARENT_REPORT_SHA)
    checked_json(review["parent_review"]["path"], review["parent_review"]["sha256"])
    base = checked_json(review["input_snapshot"]["path"], review["input_snapshot"]["sha256"])
    reference = checked_json(REFERENCE, REFERENCE_SHA)
    require(fingerprint(base) == parent["reviewed_sha256"], "Padre distinto de su evidencia")
    evidence = {r["path"]: r["sha256"] for r in review["evidence_local"]}
    proposal = checked_json(PROPOSAL, evidence[PROPOSAL])
    contexts = [{"path": path, "file_sha256": evidence[path], "payload": checked_json(path, evidence[path])}
                for path in CONTEXT_PATHS]
    oph_context = next(e for e in contexts if e["path"].endswith("opheland/context.json"))
    embedded_pages = []
    for entry in oph_context["payload"]["source_page_texts"]:
        path = Path(oph_context["path"]).parent / entry["raw_file"]
        text = (ROOT / path).read_text(encoding="utf-8")
        require(digest(text.encode()) == entry["sha256"], "Página textual de O'Phelan alterada")
        embedded_pages.append({"path": path.as_posix(), "file_sha256": digest((ROOT / path).read_bytes()),
                               "text_sha256_normalized_newlines": entry["sha256"], "text": text,
                               "printed_page": entry["printed_page"], "pdf_page": entry["pdf_page"]})
    oph_context["embedded_text_pages"] = embedded_pages
    dependencies = parent["prior_context_archives"] + [
        next(e for e in parent["outputs"] if e["path"].endswith("replacement-archive.json"))]
    prior_archives = []
    for entry in dependencies:
        payload = checked_json(entry["path"], entry["file_sha256"])
        prior_archives.append({"path": entry["path"], "file_sha256": entry["file_sha256"],
                               "canonical_json_sha256": fingerprint(payload), "payload": payload})
    require(len({e["path"] for e in prior_archives}) == 2, "Falta la cadena anterior de contextos")
    updated, archive, report = incorporate(base, reference, proposal, review, contexts, prior_archives)
    report["input_files"] = [{"path": REVIEW, "file_sha256": REVIEW_SHA},
                             {"path": PARENT_REPORT, "file_sha256": PARENT_REPORT_SHA},
                             {"path": REFERENCE, "file_sha256": REFERENCE_SHA},
                             {"path": review["input_snapshot"]["path"], "file_sha256": review["input_snapshot"]["sha256"]},
                             {"path": PROPOSAL, "file_sha256": evidence[PROPOSAL]}]
    report["builder"] = {"path": "scripts/build_corpus_snapshot_v2.py", "file_sha256": digest(Path(__file__).read_bytes())}
    return updated, archive, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Directorio nuevo dentro de outputs/")
    target = parser.parse_args().output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa un directorio nuevo dentro de outputs/; no se sobrescribe")
    updated, archive, report = build()
    payloads = {"reviewed-export.json": updated, "replacement-archive.json": archive, "build-report.json": report}
    # Serializar y verificar antes de crear el directorio final.
    encoded = {name: (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
               for name, value in payloads.items()}
    for name, value in payloads.items():
        require(json.loads(encoded[name]) == value, "La serialización cambió el resultado")
    target.mkdir(parents=True, exist_ok=False)
    for name, data in encoded.items():
        with (target / name).open("xb") as handle:
            handle.write(data)
    print(json.dumps({"status": report["status"], "split_counts": report["audit"]["split_counts"],
                      "replaced_in_place": 7, "retired_rows": 2, "training_performed": False}))


if __name__ == "__main__":
    main()
