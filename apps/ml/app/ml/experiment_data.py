"""Validación del snapshot y huellas para experimentos auditables."""
from __future__ import annotations

import hashlib
import json
from collections import Counter


def fingerprint(value: object) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_snapshot(payload: dict) -> dict:
    labels = payload.get("labels") or []
    if len(labels) < 2 or len(set(labels)) != len(labels):
        raise ValueError("Se requieren al menos dos clases únicas")
    splits = {name: [] for name in ("train", "val", "test")}
    sources: dict[str, str] = {}
    texts: dict[str, str] = {}
    for index, row in enumerate(payload.get("items") or []):
        split = row.get("split")
        if split not in splits:
            raise ValueError(f"Split inválido en fila {index}")
        if row.get("label") not in labels or not isinstance(row.get("text"), str) or not row["text"].strip():
            raise ValueError(f"Texto o etiqueta inválidos en fila {index}")
        source = row.get("resourceId")
        if not source:
            raise ValueError(f"Falta resourceId en fila {index}; no se puede auditar la separación por fuente")
        if source in sources and sources[source] != split:
            raise ValueError("Fuga de datos: una fuente aparece en varios splits")
        sources[source] = split
        digest = fingerprint(" ".join(row["text"].casefold().split()))
        if digest in texts and texts[digest] != split:
            raise ValueError("Fuga de datos: texto duplicado entre splits")
        texts[digest] = split
        splits[split].append(row)
    for split, rows in splits.items():
        absent = set(labels) - {row["label"] for row in rows}
        if absent:
            raise ValueError(f"Clases ausentes en {split}: {sorted(absent)}")
    return {
        "dataset_sha256": fingerprint(payload),
        "split_counts": {name: len(rows) for name, rows in splits.items()},
        "class_distribution": {name: dict(Counter(row["label"] for row in rows)) for name, rows in splits.items()},
        "sources_by_split": {name: sorted(key for key, value in sources.items() if value == name) for name in splits},
        "source_overlap": 0,
        "exact_text_overlap": 0,
    }
