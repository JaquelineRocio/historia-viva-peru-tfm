"""NER histórico híbrido: BETO para nombres y reglas auditables para fechas."""
import re
from functools import lru_cache
from typing import Dict, List

from app.config import settings

YEAR_RE = re.compile(r"(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)")
RANGE_RE = re.compile(
    r"(?<!\d)(1[0-9]{3}|20[0-9]{2})\s*(?:[-–—]|a|hasta)\s*(1[0-9]{3}|20[0-9]{2})(?!\d)",
    re.IGNORECASE,
)
FULL_DATE_RE = re.compile(
    r"(?<!\d)([0-3]?\d)\s+de\s+"
    r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)"
    r"(?:\s+de)?\s+(1[0-9]{3}|20[0-9]{2})(?!\d)",
    re.IGNORECASE,
)
LABEL_MAP = {"PER": "person", "LOC": "place", "ORG": "organization", "MISC": "other"}
ALIASES = {
    "jose de san martin": "José de San Martín", "san martin": "José de San Martín",
    "simon bolivar": "Simón Bolívar", "bolivar": "Simón Bolívar",
    "jose de la riva aguero": "José de la Riva-Agüero", "riva aguero": "José de la Riva-Agüero",
}
BROKEN_STANDALONE = {
    "absolu", "ctor", "depar", "eric", "gran", "gui", "her", "hist",
    "prote", "scar", "ulo", "vers",
}


@lru_cache(maxsize=1)
def _ner():
    from transformers import pipeline

    return pipeline(
        "token-classification",
        model=settings.ner_model,
        tokenizer=settings.ner_model,
        aggregation_strategy="simple",
        device=-1,
    )


def is_loaded() -> bool:
    return _ner.cache_info().currsize > 0


def _model_entities(text: str, entities: List[Dict]) -> List[Dict]:
    prepared: List[Dict] = []
    for item in entities:
        entity_type = LABEL_MAP.get(str(item.get("entity_group", "")).upper())
        score = float(item.get("score", 0))
        threshold = 0.80 if entity_type in ("person", "place") else 0.85
        if not entity_type or score < threshold:
            continue
        start, end = int(item.get("start", 0)), int(item.get("end", 0))
        mention = text[start:end].strip(" -") if 0 <= start < end <= len(text) else ""
        if not mention:
            mention = re.sub(r"\s*##\s*", "", str(item.get("word", ""))).strip(" -")
        mention = re.sub(r"\s*-\s*", "-", mention)
        prepared.append({"type": entity_type, "text": mention, "start": start, "end": end, "confidence": score})

    prepared.sort(key=lambda item: (item["start"], item["end"]))
    merged: List[Dict] = []
    for item in prepared:
        if merged and merged[-1]["type"] == item["type"]:
            previous = merged[-1]
            gap = text[previous["end"]:item["start"]] if item["start"] >= previous["end"] else ""
            connector = _without_accents(gap.casefold()).strip(" .'’-")
            joins_name = item["start"] <= previous["end"] + 1 or connector in {"", "de", "del", "de la", "de los"}
            if joins_name and item["start"] <= previous["end"] + 8:
                previous["end"] = max(previous["end"], item["end"])
                previous["text"] = text[previous["start"]:previous["end"]].strip(" -")
                previous["confidence"] = min(previous["confidence"], item["confidence"])
                continue
        merged.append(item)

    clean: List[Dict] = []
    seen = set()
    for item in merged:
        mention = " ".join(item["text"].split()).strip(" -.,;:")
        normalized = mention.casefold()
        plain = _without_accents(normalized)
        if (
            len(mention) < 3
            or plain in BROKEN_STANDALONE
            or not re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", mention)
        ):
            continue
        canonical = ALIASES.get(plain, mention)
        key = (item["type"], canonical.casefold(), item["start"], item["end"])
        if key in seen:
            continue
        seen.add(key)
        clean.append({
            "type": item["type"], "text": canonical, "normalized_value": canonical.casefold(),
            "start": item["start"], "end": item["end"], "confidence": item["confidence"],
            "year_start": None, "year_end": None, "method": "beto-ner", "out_of_scope": False,
        })
    return clean


def _temporal(text: str) -> List[Dict]:
    found: List[Dict] = []
    occupied = set()
    for match in RANGE_RE.finditer(text):
        start_year, end_year = int(match.group(1)), int(match.group(2))
        if start_year > end_year:
            start_year, end_year = end_year, start_year
        found.append({
            "type": "period", "text": match.group(0), "normalized_value": f"{start_year}-{end_year}",
            "start": match.start(), "end": match.end(), "confidence": 1.0,
            "year_start": start_year, "year_end": end_year, "method": "rule",
            "out_of_scope": start_year < 1780 or end_year > 1842,
        })
        occupied.update(range(match.start(), match.end()))
    for match in FULL_DATE_RE.finditer(text):
        year = int(match.group(3))
        found.append({
            "type": "date", "text": match.group(0), "normalized_value": match.group(0).lower(),
            "start": match.start(), "end": match.end(), "confidence": 1.0,
            "year_start": year, "year_end": year, "method": "rule",
            "out_of_scope": year < 1780 or year > 1842,
        })
        occupied.update(range(match.start(), match.end()))
    for match in YEAR_RE.finditer(text):
        if any(index in occupied for index in range(match.start(), match.end())):
            continue
        year = int(match.group(1))
        found.append({
            "type": "date", "text": match.group(0), "normalized_value": match.group(0),
            "start": match.start(), "end": match.end(), "confidence": 1.0,
            "year_start": year, "year_end": year, "method": "rule",
            "out_of_scope": year < 1780 or year > 1842,
        })
    return found


def extract(texts: List[str]) -> Dict:
    results = [_temporal(text) for text in texts]
    model_available = True
    error = None
    try:
        predictions = _ner()(texts)
        if texts and isinstance(predictions, list) and predictions and isinstance(predictions[0], dict):
            predictions = [predictions]
        for index, entities in enumerate(predictions):
            results[index].extend(_model_entities(texts[index], entities))
    except Exception as exc:
        model_available = False
        error = str(exc)
    return {
        "model": settings.ner_model,
        "model_available": model_available,
        "error": error,
        "results": results,
    }


def _without_accents(value: str) -> str:
    import unicodedata
    return "".join(char for char in unicodedata.normalize("NFD", value) if unicodedata.category(char) != "Mn")
