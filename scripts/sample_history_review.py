"""Muestra local reproducible; no entrena, cambia etiquetas ni conecta a servicios."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

METHOD = "history-review-v1"
SEED = 42


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sample_review(dataset: dict) -> dict:
    labels = sorted(dataset["labels"])
    if len(labels) != 7 or len(set(labels)) != 7 or "no_relevante" not in labels:
        raise ValueError("Esta muestra requiere la taxonomía de siete clases del proyecto")
    quotas = {label: 2 if label == "no_relevante" else 3 for label in labels}
    selected = []
    for label in labels:
        rows = [(i, r) for i, r in enumerate(dataset["items"])
                if r["split"] == "train" and r["label"] == label]
        if len(rows) < quotas[label]:
            raise ValueError(f"No hay suficientes ejemplos de entrenamiento: {label}")
        rows.sort(key=lambda pair: (
            sha256(f"{METHOD}:{SEED}\n{pair[1]['resourceId']}\n{pair[1]['text']}"),
            pair[0],
        ))
        selected.extend(rows[:quotas[label]])
    selected.sort(key=lambda pair: sha256(f"display:{SEED}:{pair[0]}"))
    canonical = json.dumps(dataset, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "method": METHOD,
        "seed": SEED,
        "dataset_sha256": sha256(canonical),
        "quotas": quotas,
        "items": [
            {
                "review_id": f"R{number:02d}",
                "item_index": index,
                "resource_id": row["resourceId"],
                "source_type": row["sourceType"],
                "split": row["split"],
                "original_label": row["label"],
                "text_sha256": sha256(row["text"]),
                "word_count": len(row["text"].split()),
            }
            for number, (index, row) in enumerate(selected, 1)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path,
                        default=Path("artifacts/datasets/gold-v1-source-aware.json"))
    parser.add_argument("--output", type=Path, required=True,
                        help="Archivo nuevo: se rechaza sobrescribir archivos existentes")
    parser.add_argument("--include-text", action="store_true",
                        help="Incluye textos solo en una salida local dentro de outputs/")
    args = parser.parse_args()
    if args.include_text and not args.output.resolve().is_relative_to(Path("outputs").resolve()):
        parser.error("Con --include-text, guarda la revisión local en outputs/")
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    sample = sample_review(dataset)
    if args.include_text:
        for row in sample["items"]:
            row["text"] = dataset["items"][row["item_index"]]["text"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        output.write(json.dumps(sample, ensure_ascii=False, indent=2) + "\n")
    print(f"Muestra generada: {len(sample['items'])} fragmentos de train")


if __name__ == "__main__":
    main()
