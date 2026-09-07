"""Aplica correcciones consensuadas de train en una copia experimental local."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/ml"))
from app.ml.experiment_data import fingerprint, validate_snapshot


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_labels(base: dict, reference: dict, review: dict, first: dict,
                 identifiers: list[str]) -> tuple[dict, dict]:
    if not identifiers or len(set(identifiers)) != len(identifiers):
        raise ValueError("Indica identificadores de revisión únicos")
    if review["status"] != "second_ai_review_recorded_not_applied":
        raise ValueError("Se requiere el segundo dictamen registrado")
    validate_snapshot(base)
    validate_snapshot(reference)
    holdout = lambda data: [r for r in data["items"] if r["split"] != "train"]
    if base["labels"] != reference["labels"] or holdout(base) != holdout(reference):
        raise ValueError("La taxonomía y la evaluación deben coincidir con la referencia congelada")
    reviews = {r["review_id"]: r for r in review["items"]}
    originals = {r["review_id"]: r for r in first["items"]}
    updated = copy.deepcopy(base)
    changes, used_indices = [], set()
    for identifier in identifiers:
        if identifier not in reviews or identifier not in originals:
            raise ValueError("Identificador de revisión desconocido")
        r, prior = reviews[identifier], originals[identifier]
        label = r["adopted_local_label"]
        if (r["adopted_local_decision"] != "corregir" or label not in base["labels"]
                or label == r["original_label"] or not r["final_decision_matches_first"]
                or any(d["decision"] != "corregir" or d["proposed_label"] != label
                       for d in (r["first_reviewer"], r["second_reviewer"], prior))):
            raise ValueError("Solo se aplican correcciones explícitas coincidentes entre revisores")
        keys = ("item_index", "resource_id", "text_sha256", "original_label", "split")
        if any(r[k] != prior[k] for k in keys):
            raise ValueError("El segundo dictamen no corresponde al primer registro")
        index = r["item_index"]
        if type(index) is not int or not 0 <= index < len(reference["items"]):
            raise ValueError("Índice original inválido")
        original = reference["items"][index]
        if (r["split"] != "train" or original["split"] != "train"
                or original["resourceId"] != r["resource_id"]
                or sha(original["text"].encode()) != r["text_sha256"]
                or original["label"] != r["original_label"]):
            raise ValueError("El registro no corresponde a una fila original de entrenamiento")
        matches = [i for i, row in enumerate(base["items"])
                   if row["resourceId"] == r["resource_id"]
                   and sha(row["text"].encode()) == r["text_sha256"]]
        if len(matches) != 1:
            raise ValueError("El fragmento debe existir una sola vez en la copia de entrada")
        current = matches[0]
        if (current in used_indices or base["items"][current]["split"] != "train"
                or base["items"][current]["label"] != r["original_label"]):
            raise ValueError("La etiqueta cambió, ya se corrigió o el destino no es train")
        used_indices.add(current)
        updated["items"][current]["label"] = label
        changes.append({"review_id": identifier, "reference_index": index, "parent_index": current,
                        "resource_id": r["resource_id"], "text_sha256": r["text_sha256"],
                        "old_label": r["original_label"], "new_label": label,
                        "reason": r["second_reviewer"]["rationale"],
                        "annotation_origin": "two_ai_reviews", "human_expert_validation": False})
    metadata = updated["dataset"]
    parent_sha, review_sha = fingerprint(base), fingerprint(review)
    metadata.update({"id": str(uuid5(NAMESPACE_URL, parent_sha + review_sha + fingerprint(changes))),
                     "name": "Experimental: correcciones históricas consensuadas",
                     "status": "experimental_local", "parent_sha256": parent_sha})
    metadata.setdefault("label_correction_history", []).append({
        "parent_sha256": parent_sha, "review_sha256": review_sha, "changes": changes})
    audit = validate_snapshot(updated)
    if holdout(updated) != holdout(reference):
        raise ValueError("La evaluación fue alterada")
    report = {"status": "experimental_local", "parent_sha256": parent_sha,
              "review_sha256": review_sha, "reference_sha256": fingerprint(reference),
              "reviewed_sha256": fingerprint(updated), "evaluation_sha256": fingerprint(holdout(updated)),
              "relabeled": len(changes), "added": 0, "removed": 0, "changes": changes,
              "audit": audit, "training_performed": False, "production_changed": False}
    return updated, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--ids", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa una carpeta nueva dentro de outputs/; no se sobrescriben resultados")
    read = lambda p: json.loads(p.read_text(encoding="utf-8"))
    base, review = read(args.base), read(args.review)
    for entry in review["inputs"].values():
        if sha((ROOT / entry["path"]).read_bytes()) != entry["file_sha256"]:
            raise ValueError(f"Entrada del dictamen alterada: {entry['path']}")
    reference = read(ROOT / review["inputs"]["dataset"]["path"])
    first = read(ROOT / review["inputs"]["first_review"]["path"])
    updated, report = apply_labels(base, reference, review, first, args.ids)
    report["inputs"] = {name: {"path": str(path.resolve().relative_to(ROOT)),
                              "file_sha256": sha(path.read_bytes())}
                        for name, path in (("base", args.base), ("review", args.review))}
    # La ruta permite localizar el archivo de contexto de la versión padre.
    report["parent_context_directory"] = str(args.base.resolve().parent.relative_to(ROOT))
    target.mkdir(parents=True, exist_ok=False)
    for name, payload in (("reviewed-export.json", updated), ("build-report.json", report)):
        with (target / name).open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"relabeled": report["relabeled"], "split_counts": report["audit"]["split_counts"]}))


if __name__ == "__main__":
    main()
