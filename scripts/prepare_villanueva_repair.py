"""Prepara una reparación local de seis filas; no modifica el dataset."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
from pathlib import Path

from pypdf import PdfReader

from prepare_agn_pilot import digest, grams, normalize, similarities

ROOT = Path(__file__).resolve().parents[1]
BOUNDARIES = ROOT / "artifacts/reviews/villanueva-boundaries-v1.json"
BOUNDARIES_SHA = "eecb567a777189571d9f9a02b2a5f824e439f43682f6cc75cd87ddfa0957fce2"
INDICES = [7, 633, 15, 14, 10, 637]
LABELS = {
    "V03": "organizacion_consecuencias_republicanas",
    "V04": "liderazgos_diplomacia_proyectos",
    "V06": "organizacion_consecuencias_republicanas",
    "V07": "organizacion_consecuencias_republicanas",
}
CHANGES = {
    "V04": [('humano "l.', 'humano ".'), ("asequible2•", "asequible.")],
    "V07": [('liberalismo"7.', 'liberalismo".')],
}


def select(raw: str, start: str, end: str) -> str:
    text = " ".join(raw.split())
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError("Marcadores ausentes o no únicos")
    first, last = text.index(start), text.index(end) + len(end)
    if first >= last:
        raise ValueError("Límites invertidos")
    return text[first:last]


def partition(text: str, markers: list[tuple[str, str]]) -> list[dict]:
    """Conserva cada carácter original, incluidos paratextos y espacios."""
    positions = []
    for marker, destination in markers:
        if text.count(marker) != 1:
            raise ValueError("Partición original no unívoca")
        positions.append((text.index(marker), destination))
    if positions[0][0] != 0 or positions != sorted(positions):
        raise ValueError("Partición incompleta o desordenada")
    result = []
    for i, (first, destination) in enumerate(positions):
        last = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        chunk = text[first:last]
        result.append(dict(destination=destination, start=first, end=last,
                           text=chunk, text_sha256=digest(chunk.encode())))
    if "".join(p["text"] for p in result) != text:
        raise ValueError("La partición perdió texto")
    return result


def prepare() -> dict:
    if digest(BOUNDARIES.read_bytes()) != BOUNDARIES_SHA:
        raise ValueError("Cambió el mapa revisado de Villanueva")
    boundary = json.loads(BOUNDARIES.read_text(encoding="utf-8"))
    for entry in boundary["inputs"]:
        if digest((ROOT / entry["path"]).read_bytes()) != entry["file_sha256"]:
            raise ValueError("Cambió una entrada del mapa")
    data = json.loads((ROOT / boundary["inputs"][0]["path"]).read_text(encoding="utf-8"))
    rows, source = data["items"], boundary["source_id"]
    for item in boundary["original_rows"] + boundary["context_rows"]:
        row = rows[item["index"]]
        if (row["split"] != "train" or row["resourceId"] != source
                or row["label"] != item["label"] or digest(row["text"].encode()) != item["text_sha256"]):
            raise ValueError("Fila revisada no coincide")
    if any(r["split"] != "train" for r in rows if r["resourceId"] == source):
        raise ValueError("La fuente está repartida entre particiones")
    pages = [p.extract_text() for p in PdfReader(ROOT / boundary["inputs"][1]["path"]).pages]
    units = []
    for original in boundary["units"]:
        parts = []
        for part in original["parts"]:
            raw = pages[part["pdf_page"] - 1]
            extracted = select(raw, part["start_marker"], part["end_marker"])
            if digest(raw.encode()) != part["page_text_sha256"] or digest(extracted.encode()) != part["selected_text_sha256"]:
                raise ValueError("Extracción no reproduce el mapa")
            parts.append(extracted)
        text = " ".join(parts)
        if digest(text.encode()) != original["text_sha256"]:
            raise ValueError("Unidad no reproduce el mapa")
        units.append(dict(id=original["id"], parts=original["parts"], raw_text=text))
    for uid, page, start, end in [
        ("V07", 5, 'Las "Bases para la Constitución Política"', 'liberalismo"7.'),
        ("V08", 2, "En esta línea", "las ideas expuestas en"),
    ]:
        raw = pages[page - 1]
        text = select(raw, start, end)
        units.append(dict(id=uid, raw_text=text, parts=[dict(pdf_page=page, printed_page=426 + page,
                          start_marker=start, end_marker=end, page_text_sha256=digest(raw.encode()),
                          selected_text_sha256=digest(text.encode()))]))
    for unit in units:
        uid, text = unit["id"], unit["raw_text"]
        changes = CHANGES.get(uid, [])
        for old, new in changes:
            if text.count(old) != 1:
                raise ValueError("Ajuste de nota no coincide")
            text = text.replace(old, new)
        unit.update(text=text, text_sha256=digest(text.encode()), raw_text_sha256=digest(unit["raw_text"].encode()),
                    word_count=len(text.split()), changes=[dict(old=a, new=b) for a, b in changes],
                    proposed_label=LABELS.get(uid), disposition="candidate" if uid in LABELS else "context_only",
                    dataset_applied=False)
        if uid in LABELS and not 120 <= unit["word_count"] <= 250:
            raise ValueError("Candidato fuera de 120–250 palabras")
    cuts = {
        7: [('LA CONSTITUCIÓN', 'paratext'), ('Al estudiar', 'V01'), ('Es interesante', 'V02')],
        633: [('Esos antecedentes', 'V02'), ('Así, el Congreso', 'V03'), ('BIRA 23', 'paratext')],
        15: [('LA CONSTITUOÓNDE', 'paratext'), ('la argentina', 'V03'), ('El Manifiesto', 'V04')],
        14: [('Las manifestaciones', 'V05'), ('El Congreso General', 'V06')],
        10: [('y 5 propietarios.', 'V06'), ('Las "Bases', 'V07')],
        637: [('Más explícitamente', 'V04'), ('En esta línea', 'V08')],
    }
    archive = [dict(index=i, row=rows[i], text_sha256=digest(rows[i]["text"].encode()),
                    partitions=partition(rows[i]["text"], cuts[i])) for i in INDICES]
    # La capa PDF y el export difieren en espacios/puntuación; exigir la misma
    # secuencia de letras y números antes de aplicar los ajustes documentados.
    canonical = lambda text: re.sub(r"\W+", "", text.casefold())
    for unit in units:
        original = "".join(part["text"] for entry in archive for part in entry["partitions"]
                           if part["destination"] == unit["id"])
        if canonical(original) != canonical(unit["raw_text"]):
            raise ValueError("La unidad no conserva el contenido de sus originales")
    candidates = [u for u in units if u["disposition"] == "candidate"]
    remaining_train = [(i, r) for i, r in enumerate(rows) if r["split"] == "train" and i not in INDICES]
    for unit in candidates:
        flagged, exact = [], []
        for i, row in remaining_train:
            j, c = similarities(grams(unit["text"]), grams(row["text"]))
            if normalize(unit["text"]) == normalize(row["text"]):
                exact.append(i)
            if j >= .25 or c >= .8:
                flagged.append(dict(index=i, jaccard=round(j, 6), containment=round(c, 6)))
        unit["remaining_train_screen"] = dict(compared=len(remaining_train), exact_matches=exact, flagged=flagged)
    pairs = []
    for i, a in enumerate(candidates):
        for b in candidates[i + 1:]:
            j, c = similarities(grams(a["text"]), grams(b["text"]))
            pairs.append(dict(ids=[a["id"], b["id"]], exact=normalize(a["text"]) == normalize(b["text"]),
                              jaccard=round(j, 6), containment=round(c, 6)))
    for entry in boundary["inputs"]:
        if digest((ROOT / entry["path"]).read_bytes()) != entry["file_sha256"]:
            raise ValueError("Una entrada cambió durante la preparación")
    return dict(schema_version=1, status="proposal_not_applied", inputs=boundary["inputs"],
                boundary_manifest_sha256=BOUNDARIES_SHA, source=boundary["source"], source_id=source,
                pypdf_version=importlib.metadata.version("pypdf"), remove_indices=INDICES,
                units=units, original_archive=archive, candidate_pair_screen=pairs,
                checks=dict(original_partition_lossless=True, all_units_match_original_alphanumeric_content=True,
                            reviewed_rows_same_source_train=True, input_hashes_unchanged=True),
                screening_rule="Train remaining after proposed removal only; normalized five-word shingles, Jaccard >= .25 or containment >= .8. Not proof of absence of all partial overlap.",
                page_archive=[dict(pdf_page=i+1, text=pages[i], text_sha256=digest(pages[i].encode())) for i in [0,1,2,3,4,7,8]],
                dataset_applied=False, production_changed=False, new_metrics=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        parser.error("Usa un archivo nuevo dentro de outputs/; no se sobrescribe")
    result = prepare()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"status": result["status"], "candidates": list(LABELS), "originals_archived": len(result["original_archive"])}))


if __name__ == "__main__":
    main()
