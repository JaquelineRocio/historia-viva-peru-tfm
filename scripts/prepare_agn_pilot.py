"""Extrae tres candidatos locales del PDF fijado; no entrena ni cambia snapshots."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import unicodedata
from itertools import combinations
from pathlib import Path

from pypdf import PdfReader

PDF_SHA = "65a271f2016780bf621b9040d7409bff3fd745a28524b76662d5266243986602"
DATASET_SHA = "dcd8d90081973b7b9a05ee6ef41623756a06232727f3718268945d71a207310a"
SPECS = [
    ("AGN01", 7, "Además, como parte", "Se le dio el nombre de su propietaria: Josefa.",
     "contexto_colonial_antecedentes", 1805, "venta-josefa-1805",
     [("[pesos]5.", "[pesos]."), ("Bretaña 6.", "Bretaña.")]),
    ("AGN02", 21, "Y estando presente", "prevenidas por derecho.",
     "participacion_social_regional", 1834, "solar-cofradia-1834-1836",
     [("// [fol. 457]", "")]),
    ("AGN03", 22, "En Lima Abril", "Don Francisco Garay.",
     "participacion_social_regional", 1836, "solar-cofradia-1834-1836", []),
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return " ".join(re.findall(r"\w+", "".join(
        c for c in decomposed if not unicodedata.combining(c))))


def grams(text: str) -> set[tuple[str, ...]]:
    words = normalize(text).split()
    return {tuple(words[i:i + 5]) for i in range(len(words) - 4)}


def similarities(a: set, b: set) -> tuple[float, float]:
    common = len(a & b)
    return (common / len(a | b) if a | b else 0.0,
            common / min(len(a), len(b)) if a and b else 0.0)


def extract(page: str, start: str, end: str, replacements: list) -> tuple[str, str]:
    # Reunir palabras partidas por guion de fin de línea, conservando la grafía.
    joined = " ".join(re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", page).split())
    if joined.count(start) != 1 or joined.count(end) != 1:
        raise ValueError("Los límites del pasaje no son únicos")
    first = joined.index(start)
    last = joined.index(end, first) + len(end)
    selected = joined[first:last]
    text = selected
    for old, new in replacements:
        if text.count(old) != 1:
            raise ValueError("El ajuste de extracción no coincide exactamente")
        text = text.replace(old, new)
    text = " ".join(text.split())
    if not 120 <= len(text.split()) <= 250:
        raise ValueError("El fragmento no cumple 120–250 palabras")
    return selected, text


def prepare(pdf_path: Path, dataset_path: Path) -> dict:
    pdf_bytes, dataset_bytes = pdf_path.read_bytes(), dataset_path.read_bytes()
    if digest(pdf_bytes) != PDF_SHA or digest(dataset_bytes) != DATASET_SHA:
        raise ValueError("El PDF o snapshot no coincide con la versión revisada")
    reader = PdfReader(pdf_path)
    dataset = json.loads(dataset_bytes)
    # Comparación mecánica en todos los splits; no se exportan textos de evaluación.
    references = [(i, row["split"], normalize(row["text"]), grams(row["text"]))
                  for i, row in enumerate(dataset["items"])]
    items = []
    for identifier, page, start, end, label, year, group, changes in SPECS:
        if label not in dataset["labels"]:
            raise ValueError("Etiqueta fuera de la taxonomía")
        page_text = reader.pages[page - 1].extract_text()
        selected, text = extract(page_text, start, end, changes)
        shingles = grams(text)
        screening = {}
        for split in ("train", "val", "test"):
            scores, exact, flagged = [], [], []
            for index, part, normalized, other in references:
                if part != split:
                    continue
                jaccard, containment = similarities(shingles, other)
                scores.append((jaccard, containment))
                if normalize(text) == normalized:
                    exact.append(index)
                if jaccard >= 0.25 or containment >= 0.8:
                    flagged.append(index)
            screening[split] = {
                "compared": len(scores), "exact_matches": exact, "flagged_indices": flagged,
                "max_jaccard": round(max(s[0] for s in scores), 6),
                "max_containment": round(max(s[1] for s in scores), 6),
            }
        items.append({
            "id": identifier, "pdf_page": page, "printed_page": page + 14,
            "page_text_sha256": digest(page_text.encode()),
            "selection_sha256": digest(selected.encode()), "text_sha256": digest(text.encode()),
            "start_marker": start, "end_marker": end,
            "extraction_changes": [{"old": a, "new": b} for a, b in changes],
            "word_count": len(text.split()), "historical_year": year,
            "related_document_group": group,
            "source_group": "doi:10.37840/ragn.v32i1.5",
            "proposed_label": label, "split": None, "review_status": "pending_author_review",
            "applied": False, "overlap_screen": screening,
            "selected_text_before_marker_removal": selected, "text": text,
        })
    pairs = []
    for a, b in combinations(items, 2):
        jaccard, containment = similarities(grams(a["text"]), grams(b["text"]))
        pairs.append({"ids": [a["id"], b["id"]], "jaccard": round(jaccard, 6),
                      "containment": round(containment, 6),
                      "same_document_group": a["related_document_group"] == b["related_document_group"]})
    return {"pdf_sha256": PDF_SHA, "dataset_file_sha256": DATASET_SHA,
            "pypdf_version": importlib.metadata.version("pypdf"),
            "normalization": "NFKD/casefold, accents removed, word tokens; sets of 5-word sequences",
            "flag_rule": "Jaccard >= 0.25 OR overlap / smaller set >= 0.8",
            "screening_limit": "Lexical screening only; not proof of independence or absence of paraphrase",
            "items": items, "within_pilot": pairs}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=Path("outputs/source-candidates-v1/josefa-montes.pdf"))
    parser.add_argument("--dataset", type=Path, default=Path("artifacts/datasets/gold-v1-source-aware.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(Path("outputs").resolve()):
        parser.error("El texto completo debe guardarse localmente en outputs/")
    if args.output.exists():
        parser.error("La salida ya existe; utiliza un nombre nuevo")
    payload = prepare(args.pdf, args.dataset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        output.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"Preparados {len(payload['items'])} candidatos locales; dataset intacto")


if __name__ == "__main__":
    main()
