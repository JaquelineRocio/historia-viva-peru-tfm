"""Modelo activo en memoria: carga e inferencia con BETO fine-tuneado.

Todas las dependencias pesadas (torch, transformers) se importan de forma
perezosa para que el servicio arranque sin ellas (solo se necesitan al entrenar
o inferir). El modelo activo se cachea en un singleton.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

BETO_BASE = "dccuchile/bert-base-spanish-wwm-cased"

_active: Optional["_LoadedModel"] = None


class _LoadedModel:
    def __init__(self, model, tokenizer, id2label: Dict[int, str], max_len: int):
        self.model = model
        self.tokenizer = tokenizer
        self.id2label = id2label
        self.max_len = max_len


def load_model(artifact_path: str) -> List[str]:
    """Carga el modelo/tokenizer/label-map desde artifact_path como modelo activo."""
    global _active
    import torch  # noqa: F401  (lazy)
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    if not os.path.isdir(artifact_path):
        raise FileNotFoundError(f"No existe el artefacto del modelo: {artifact_path}")

    with open(os.path.join(artifact_path, "labels.json"), "r", encoding="utf-8") as fh:
        meta = json.load(fh)
    id2label = {int(k): v for k, v in meta["id2label"].items()}
    max_len = int(meta.get("max_len", 192))

    tokenizer = AutoTokenizer.from_pretrained(artifact_path)
    model = AutoModelForSequenceClassification.from_pretrained(artifact_path)
    model.eval()
    _active = _LoadedModel(model, tokenizer, id2label, max_len)
    return [id2label[i] for i in sorted(id2label)]


def is_loaded() -> bool:
    return _active is not None


def infer(texts: List[str]) -> List[dict]:
    """Clasifica textos con el modelo activo. Devuelve [{label, confidence}]."""
    if _active is None:
        raise RuntimeError("No hay modelo activo cargado")
    import torch

    preds: List[dict] = []
    bs = 16
    for i in range(0, len(texts), bs):
        batch = texts[i : i + bs]
        enc = _active.tokenizer(
            batch, truncation=True, padding=True, max_length=_active.max_len, return_tensors="pt"
        )
        with torch.no_grad():
            logits = _active.model(**enc).logits
            probs = torch.softmax(logits, dim=-1)
            conf, idx = torch.max(probs, dim=-1)
        for c, ix in zip(conf.tolist(), idx.tolist()):
            preds.append({"label": _active.id2label[int(ix)], "confidence": round(float(c), 4)})
    return preds
