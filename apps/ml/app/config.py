"""Configuración del servicio ML (variables de entorno)."""
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Directorio base del servicio (apps/ml), independiente del cwd desde el que se arranque.
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ML_", extra="ignore")

    # Servidor
    host: str = "0.0.0.0"
    port: int = 8000

    # Idiomas preferidos para subtítulos de YouTube (orden de prioridad)
    transcript_languages: List[str] = ["es", "es-PE", "es-419", "es-ES"]

    # Almacenamiento de artefactos (relativo a BASE_DIR salvo ruta absoluta)
    storage_dir: str = "storage"

    # Fallback Whisper (faster-whisper). Modelos: tiny|base|small|medium|large-v3.
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"     # int8 = ligero para CPU
    whisper_language: str = "es"

    # Token compartido para que solo NestJS pueda llamar al servicio ML
    internal_token: Optional[str] = None

    # Modelo multilingüe para recuperación semántica (384 dimensiones).
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ner_model: str = "mrm8488/bert-spanish-cased-finetuned-ner"
    default_model_repo: Optional[str] = None
    default_model_path: str = "storage/models/beto-v1-gold-source-aware"

    def storage_root(self) -> Path:
        p = Path(self.storage_dir)
        return p.resolve() if p.is_absolute() else (BASE_DIR / p).resolve()


settings = Settings()


def resolve_storage_path(path_str: str) -> Path:
    """Resuelve una ruta de artefacto bajo el directorio de almacenamiento.

    Las rutas relativas se anclan a BASE_DIR (apps/ml), no al cwd, y se acepta
    el `storage/...` que envía NestJS. Lanza ValueError si la ruta resultante
    escapa del almacenamiento (path traversal).
    """
    root = settings.storage_root()
    p = Path(path_str)
    resolved = p.resolve() if p.is_absolute() else (BASE_DIR / p).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ValueError(f"Ruta fuera del almacenamiento permitido: {path_str}")
    return resolved
