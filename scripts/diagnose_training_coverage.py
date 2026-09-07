"""Diagnóstico descriptivo de train y coeficientes; no predice ni cambia etiquetas."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ("crisis_ideas_emancipadoras", "organizacion_consecuencias_republicanas")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def describe(data: dict) -> dict:
    rows = [(i, r) for i, r in enumerate(data["items"]) if r["split"] == "train"]
    sources, classes = defaultdict(Counter), Counter()
    duplicate_groups = defaultdict(list)
    pdf_length_flags = []
    for i, row in rows:
        sources[row["resourceId"]][row["label"]] += 1
        classes[row["label"]] += 1
        duplicate_groups[(row["resourceId"], " ".join(row["text"].casefold().split()))].append(i)
        words = len(row["text"].split())
        if row["sourceType"] == "pdf" and not 120 <= words <= 250:
            pdf_length_flags.append({"index": i, "label": row["label"], "words": words})
    sample, target_summary = [], {}
    for label in TARGETS:
        distribution = {s: counts[label] for s, counts in sorted(sources.items()) if counts[label]}
        for source in distribution:
            candidates = [(i, r) for i, r in rows if r["label"] == label and r["resourceId"] == source]
            candidates.sort(key=lambda pair: digest(("coverage-v1:" + str(pair[0]) + ":" + pair[1]["text"]).encode()))
            sample.extend({"index": i, "resource_id": source, "label": label,
                           "text_sha256": digest(r["text"].encode()), "words": len(r["text"].split())}
                          for i, r in candidates[:2])
        label_rows = [r for _, r in rows if r["label"] == label]
        total = len(label_rows)
        target_summary[label] = {
            "rows": total, "sources": distribution,
            "top_two_source_share": round(sum(sorted(distribution.values(), reverse=True)[:2]) / total, 6),
            "source_types": dict(Counter(r["sourceType"] for r in label_rows)),
            "literal_eh_rows": sum(bool(re.search(r"\beh\b", r["text"], re.I)) for r in label_rows),
            "literal_de_de_rows": sum(bool(re.search(r"\bde\s+de\b", r["text"], re.I)) for r in label_rows),
        }
    return {"train_rows": len(rows), "class_counts": dict(classes),
            "source_class_counts": {s: dict(counts) for s, counts in sorted(sources.items())},
            "source_types": dict(Counter(r["sourceType"] for _, r in rows)),
            "target_summary": target_summary,
            "duplicate_same_source_text_indices": [ids for ids in duplicate_groups.values() if len(ids) > 1],
            "pdf_outside_length_guideline": pdf_length_flags,
            "sample_method": "First two per available source and target label by SHA256(coverage-v1:index:text); train only, labels visible.",
            "sample": sample}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dataset", "model-report", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa un archivo nuevo dentro de outputs/; no se sobrescriben resultados")
    data = json.loads(args.dataset.read_text(encoding="utf-8"))
    report = json.loads(args.model_report.read_text(encoding="utf-8"))
    if digest(args.dataset.read_bytes()) != report["inputs"]["after"]["file_sha256"]:
        raise ValueError("El dataset no corresponde al modelo analizado")
    entry = report["runs"]["after"]["model"]
    model_path = ROOT / entry["path"]
    if digest(model_path.read_bytes()) != entry["file_sha256"]:
        raise ValueError("El modelo local cambió desde su entrenamiento")
    import joblib
    model = joblib.load(model_path)  # Artefacto local propio, con hash verificado.
    features = model["tfidf"].get_feature_names_out()
    classifier = model["classifier"]
    result = describe(data)
    result["top_positive_coefficients"] = {}
    for label in TARGETS:
        index = classifier.classes_.tolist().index(label)
        top = classifier.coef_[index].argsort()[-15:][::-1]
        result["top_positive_coefficients"][label] = [
            {"term": features[j], "coefficient": round(float(classifier.coef_[index, j]), 6)} for j in top]
    result["inputs"] = {name: {"path": path.resolve().relative_to(ROOT).as_posix(),
                              "file_sha256": digest(path.read_bytes())}
                        for name, path in (("dataset", args.dataset), ("model_report", args.model_report),
                                           ("model", model_path), ("script", Path(__file__)))}
    result["limits"] = ["Descriptive source concentration is not proof of error causation.",
                       "Coefficients are not calibrated probabilities or explanations of a particular prediction.",
                       "Length flags identify candidates for review, not automatically invalid examples.",
                       "The sample is source-stratified, not a representative error-rate estimate."]
    result.update({"dataset_changed": False, "training_performed": False, "predictions_performed": False})
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"train_rows": result["train_rows"], "sample_size": len(result["sample"]),
                      "length_flags": len(result["pdf_outside_length_guideline"])}))


if __name__ == "__main__":
    main()
