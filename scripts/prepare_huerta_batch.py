"""Extrae un lote pequeño de Huerta para revisión; no incorpora filas ni entrena."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from itertools import combinations
from pathlib import Path

from pypdf import PdfReader
from prepare_agn_pilot import digest, extract, grams, normalize, similarities

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    "source_review": {"path": "artifacts/reviews/huerta-pilot-v1.json",
                      "file_sha256": "add75d193013f9ff94581b2f2a026857b135c3e9caf6246d5d2034308202e1c0"},
    "dataset": {"path": "outputs/huerta-snapshot-v1/reviewed-export.json",
                "file_sha256": "eb1442c51b09dd66f691d77c6d9e412f5bebdef153e9b4efb6a30c905c03293b"},
}
SPECS = [
    ("HUE02", 14, "El carácter propagandístico", "Libertad de los Pueblos Soberanos.35",
     [("Soberanos.35", "Soberanos.")], "35 Gaceta", "GGLI/t1/n5/1821-07-25/p18"),
    ("HUE03", 16, "Además del interés oficial", "uno de los mejores escritos».41",
     [("1818».40", "1818»."), ("escritos».41", "escritos»."), ("T omás", "Tomás")],
     "40 Carta", "AGN/ColeccionTomasDieguez/2.7.22/f1r/1821-10-14"),
    ("HUE04", 17, "Antes del colapso", "acceso directo al material impreso.",
     [("otros. 42", "otros.")], "42 Álvarez", "Huerta2020/p141/prensa-fidelista-patriota"),
]


def prepare() -> dict:
    read = lambda path: json.loads(path.read_text(encoding="utf-8"))
    for entry in INPUTS.values():
        if digest((ROOT / entry["path"]).read_bytes()) != entry["file_sha256"]:
            raise ValueError(f"Entrada alterada: {entry['path']}")
    prior = read(ROOT / INPUTS["source_review"]["path"])
    inputs = {**INPUTS, **{k: prior["inputs"][k] for k in ("pdf", "taxonomy", "overlap_helpers")}}
    for entry in inputs.values():
        if digest((ROOT / entry["path"]).read_bytes()) != entry["file_sha256"]:
            raise ValueError(f"Entrada alterada: {entry['path']}")
    reader = PdfReader(ROOT / inputs["pdf"]["path"])
    dataset = read(ROOT / inputs["dataset"]["path"])
    label = "crisis_ideas_emancipadoras"
    if label not in dataset["labels"]:
        raise ValueError("Etiqueta fuera de la taxonomía")
    comparisons = [(i, r["split"], normalize(r["text"]), grams(r["text"]))
                   for i, r in enumerate(dataset["items"])]
    items = []
    for identifier, page, start, end, changes, note_start, group in SPECS:
        raw = reader.pages[page - 1].extract_text()
        selected, text = extract(raw, start, end, changes)
        if raw.count(note_start) != 1:
            raise ValueError("No se localizó la atribución de forma única")
        screening = {}
        for split in ("train", "val", "test"):
            scores, exact, flagged = [], [], []
            for index, part, normalized, other in comparisons:
                if part != split:
                    continue
                j, c = similarities(grams(text), other)
                scores.append((j, c))
                if normalize(text) == normalized:
                    exact.append(index)
                if j >= .25 or c >= .8:
                    flagged.append(index)
            screening[split] = {"compared": len(scores), "exact_matches": exact,
                               "flagged_indices": flagged,
                               "max_jaccard": round(max(s[0] for s in scores), 6),
                               "max_containment": round(max(s[1] for s in scores), 6)}
        items.append({"id": identifier, "pdf_page": page, "printed_page": page + 124,
                      "start_marker": start, "end_marker": end,
                      "extraction_changes": [{"old": a, "new": b} for a, b in changes],
                      "selected_text": selected, "text": text, "word_count": len(text.split()),
                      "text_sha256": digest(text.encode()), "page_text_sha256": digest(raw.encode()),
                      "proposed_label": label, "annotation_status": "pending_review",
                      "source_group": prior["source_group"], "document_group": group,
                      "source_split": "train", "dataset_applied": False,
                      "attribution_notes": raw[raw.index(note_start):].strip(),
                      "overlap_screen": screening,
                      "context_pdf_pages": list(range(page - 1, page + 2))})
    pages = sorted({p for item in items for p in item["context_pdf_pages"]})
    pairwise = [{"ids": [a["id"], b["id"]],
                 "jaccard_containment": similarities(grams(a["text"]), grams(b["text"]))}
                for a, b in combinations(items, 2)]
    return {"status": "local_candidates_pending_review", "inputs": inputs,
            "source": prior["source"], "source_split": "train",
            "pypdf_version": importlib.metadata.version("pypdf"), "items": items,
            "pairwise_overlap": pairwise,
            "context_pages": [{"pdf_page": p, "printed_page": p + 124,
                               "text": reader.pages[p - 1].extract_text(),
                               "text_sha256": digest(reader.pages[p - 1].extract_text().encode())}
                              for p in pages],
            "training_performed": False, "production_changed": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Archivo nuevo dentro de outputs/")
    target = parser.parse_args().output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa un archivo nuevo dentro de outputs/; no se sobrescriben resultados")
    result = prepare()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"candidates": [{"id": r["id"], "words": r["word_count"]}
                                     for r in result["items"]], "dataset_applied": False}))


if __name__ == "__main__":
    main()
