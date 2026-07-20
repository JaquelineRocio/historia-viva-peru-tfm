"""Embeddings multilingües cargados de forma perezosa."""
from functools import lru_cache
from typing import List

from app.config import settings


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def is_loaded() -> bool:
    return _model.cache_info().currsize > 0


def encode(texts: List[str]) -> List[List[float]]:
    if not texts or len(texts) > 64:
        raise ValueError("Se requieren entre 1 y 64 textos")
    vectors = _model().encode(
        texts,
        batch_size=min(16, len(texts)),
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    if vectors.shape[1] != 384:
        raise ValueError(f"El modelo devolvió {vectors.shape[1]} dimensiones; se esperaban 384")
    return vectors.astype("float32").tolist()
