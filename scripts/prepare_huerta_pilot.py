"""Prepara un candidato local de Huerta con contexto; no incorpora filas ni entrena."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

from pypdf import PdfReader

from prepare_agn_pilot import digest, extract, grams, normalize, similarities

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "artifacts/reviews/ideas-source-v1.json"
SOURCE_SHA = "644f52397a5c9d5e606939c8bf0c586e1ff2336fc8e631354b346e28a8fab4e7"
QUOTE_START = "Nuestros corazones deben ser penetrados"


def prepare() -> dict:
    if digest(SOURCE_PATH.read_bytes()) != SOURCE_SHA:
        raise ValueError("La ficha de fuente cambió; revisar antes de extraer")
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    for entry in source["inputs"].values():
        if digest((ROOT / entry["path"]).read_bytes()) != entry["file_sha256"]:
            raise ValueError(f"Entrada de la revisión alterada: {entry['path']}")
    passage = source["provisional_passages"][0]
    probe = passage["screening_probe"]
    reader = PdfReader(ROOT / source["inputs"]["pdf"]["path"])
    page = reader.pages[passage["pdf_page"] - 1].extract_text()
    changes = [("Dominio.58", "Dominio.")]
    selected, text = extract(page, probe["start_marker"], probe["end_marker"], changes)
    if digest(text.encode()) != probe["probe_sha256"] or len(text.split()) != probe["words"]:
        raise ValueError("El candidato no coincide con el pasaje seleccionado")
    if text.count(QUOTE_START) != 1 or page.count("58 Proclama del cura") != 1:
        raise ValueError("La cita y su atribución deben poder localizarse sin ambigüedad")
    commentary, quote = text.split(QUOTE_START)
    quotation = QUOTE_START + quote
    note = page[page.index("58 Proclama del cura"):].strip()
    dataset = json.loads((ROOT / source["inputs"]["dataset"]["path"]).read_text(encoding="utf-8"))
    label = passage["proposed_label"]
    if label not in dataset["labels"]:
        raise ValueError("Etiqueta fuera de la taxonomía")
    candidate_grams = grams(text)
    screening = {}
    for split in ("train", "val", "test"):
        scores, exact, flagged = [], [], []
        for index, row in enumerate(dataset["items"]):
            if row["split"] != split:
                continue
            j, c = similarities(candidate_grams, grams(row["text"]))
            scores.append((j, c))
            if normalize(text) == normalize(row["text"]):
                exact.append(index)
            if j >= 0.25 or c >= 0.8:
                flagged.append(index)
        screening[split] = {"compared": len(scores), "exact_matches": exact,
                           "flagged_indices": flagged,
                           "max_jaccard": round(max(s[0] for s in scores), 6),
                           "max_containment": round(max(s[1] for s in scores), 6)}
    return {
        "candidate_id": "HUE01", "kind": "local_candidate", "proposed_label": label,
        "source_review_file_sha256": SOURCE_SHA, "inputs": source["inputs"],
        "source": source["selected_source"], "source_group": source["selected_source"]["source_group"],
        "document_group": "AAL/Emancipacion/CurasPatriotas/Proclamas/leg1/exp1/f2r-v/1822-02-21",
        "archival_reference": passage["archival_reference"],
        "pdf_page": passage["pdf_page"], "printed_page": passage["printed_page"],
        "pypdf_version": importlib.metadata.version("pypdf"),
        "page_text_sha256": digest(page.encode()), "selection_sha256": digest(selected.encode()),
        "start_marker": probe["start_marker"], "end_marker": probe["end_marker"],
        "extraction_changes": [{"old": a, "new": b} for a, b in changes],
        "normalization": "Unir palabras partidas por guion de fin de línea y espacios; retirar solo llamada58. Conservar grafía, mayúsculas y atribuciones.",
        "selected_text_before_marker_removal": selected, "text": text,
        "text_sha256": digest(text.encode()), "word_count": len(text.split()),
        "author_commentary": commentary.strip(), "documentary_quotation": quotation,
        "attribution_note_text": note,
        "context_pages": [{"pdf_page": i, "printed_page": i + 124,
                           "text_sha256": digest(reader.pages[i - 1].extract_text().encode()),
                           "text": reader.pages[i - 1].extract_text()} for i in (20, 21, 22)],
        "overlap_screen": screening,
        "screening_rule": "5-gramas NFKD/casefold sin tildes; Jaccard >= 0.25 o containment >= 0.8",
        "screening_limit": "La comparación léxica no demuestra independencia documental ni ausencia de paráfrasis.",
        "quality_flags": ["anaphora_without_explicit_antecedent_in_quotation", "historical_spelling"],
        "assigned_split": None, "dataset_applied": False, "production_changed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Archivo nuevo dentro de outputs/")
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa un archivo nuevo dentro de outputs/; no se sobrescriben resultados")
    candidate = prepare()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as output:
        output.write(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"candidate_id": candidate["candidate_id"], "words": candidate["word_count"],
                      "proposed_label": candidate["proposed_label"], "dataset_applied": False}))


if __name__ == "__main__":
    main()
