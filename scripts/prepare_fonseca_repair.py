"""Recupera R05 entre dos páginas; prepara un candidato local sin aplicar reemplazos."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
from pathlib import Path

from pypdf import PdfReader

from prepare_agn_pilot import digest, grams, normalize, similarities

ROOT = Path(__file__).resolve().parents[1]
PEER_PATH = ROOT / "artifacts/reviews/history-review-v1-peer-review.json"
PEER_SHA = "e1aaf47ed45119a50c54127476fc33aefbca2a49097a4308cabc9d9f10a68f83"
SOURCE_ID = "e32181bc-41d0-4400-a76d-eb11fc88bf71"
PARTS = [
    (4, 108, "Además de la CDIP", "Esta afirmación es significativa, pues refuerza la"),
    (5, 109, "visión oficial", "desdibujado por su salvajismo."),
]
CHANGES = [
    ("CDIP ,", "CDIP,"),
    ("Quirós. 5 También", "Quirós. También"),
    ("Arenales6", "Arenales"),
    ("historiografía. 7 Finalmente", "historiografía. Finalmente"),
    ("matar. 8 Esta", "matar. Esta"),
]


def select(page: str, start: str, end: str) -> str:
    joined = " ".join(re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", page).split())
    if joined.count(start) != 1 or joined.count(end) != 1:
        raise ValueError("Los límites de extracción no son únicos")
    first = joined.index(start)
    return joined[first:joined.index(end, first) + len(end)]


def prepare() -> dict:
    if digest(PEER_PATH.read_bytes()) != PEER_SHA:
        raise ValueError("El segundo dictamen cambió; revisar antes de reconstruir R05")
    peer = json.loads(PEER_PATH.read_text(encoding="utf-8"))
    for entry in peer["inputs"].values():
        if digest((ROOT / entry["path"]).read_bytes()) != entry["file_sha256"]:
            raise ValueError(f"Entrada revisada alterada: {entry['path']}")
    dataset = json.loads((ROOT / peer["inputs"]["dataset"]["path"]).read_text(encoding="utf-8"))
    first = json.loads((ROOT / peer["inputs"]["first_review"]["path"]).read_text(encoding="utf-8"))
    r05 = next(r for r in peer["items"] if r["review_id"] == "R05")
    if r05["adopted_local_decision"] != "excluir" or r05["dataset_applied"]:
        raise ValueError("La decisión de R05 no coincide con esta reparación")
    reader = PdfReader(ROOT / peer["inputs"]["fonseca"]["path"])
    parts = []
    for pdf_page, printed_page, start, end in PARTS:
        page = reader.pages[pdf_page - 1].extract_text()
        selected = select(page, start, end)
        parts.append({"pdf_page": pdf_page, "printed_page": printed_page,
                      "start_marker": start, "end_marker": end,
                      "page_text_sha256": digest(page.encode()),
                      "selected_text_sha256": digest(selected.encode()), "selected_text": selected})
    selected = " ".join(p["selected_text"] for p in parts)
    text = selected
    for old, new in CHANGES:
        if text.count(old) != 1:
            raise ValueError("El ajuste de extracción no coincide exactamente")
        text = text.replace(old, new)
    if not 120 <= len(text.split()) <= 250:
        raise ValueError("El candidato debe tener 120–250 palabras")
    group = []
    for index in (55, 57, 58):
        row = dataset["items"][index]
        if row["resourceId"] != SOURCE_ID or row["split"] != "train":
            raise ValueError("El grupo documental debe conservar la misma fuente en train")
        j, c = similarities(grams(text), grams(row["text"]))
        group.append({"item_index": index, "text_sha256": digest(row["text"].encode()),
                      "label": row["label"], "jaccard": round(j, 6), "containment": round(c, 6)})
    screening = {}
    candidate_grams = grams(text)
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
        "candidate_id": "FON-R05-v1", "status": "pending_group_replacement",
        "source": first["sources"]["FON"], "source_id": SOURCE_ID,
        "source_split": "train", "proposed_label": "participacion_social_regional",
        "peer_review_file_sha256": PEER_SHA, "inputs": peer["inputs"],
        "pypdf_version": importlib.metadata.version("pypdf"), "parts": parts,
        "extraction_changes": [{"old": a, "new": b} for a, b in CHANGES],
        "word_count": len(text.split()), "text_sha256": digest(text.encode()), "text": text,
        "normalization": "Unir guiones de fin de línea y espacios; quitar llamadas 5–8 y coma separada de CDIP.",
        "overlap_screen": screening, "documentary_overlap_group": group,
        "screening_rule": "5-gramas normalizados; Jaccard >= 0.25 o containment >= 0.8",
        "screening_limit": "El umbral no detecta todos los tramos compartidos; conservar también el grupo documental.",
        "next_action": "Resolver conjuntamente train55/57/58 antes de sustituir; no añadir como contenido nuevo.",
        "dataset_applied": False, "production_changed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Archivo nuevo dentro de outputs/")
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa un archivo nuevo dentro de outputs/; no se sobrescriben resultados")
    result = prepare()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("candidate_id", "status", "word_count")}))


if __name__ == "__main__":
    main()
