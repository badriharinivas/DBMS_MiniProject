"""Lazy, validated embeddings for the shared pgvector(384) space."""

import math
import threading
import unicodedata
from typing import Protocol

EMBEDDING_DIMENSION = 384
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingUnavailableError(RuntimeError):
    """Raised when the configured embedding model cannot produce a vector."""


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]:
        """Return one normalized 384-dimensional embedding for text."""


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        raise ValueError("Embedding input must be text")
    normalized = " ".join(unicodedata.normalize("NFKC", text).split())
    if not normalized:
        raise ValueError("Embedding input cannot be empty")
    return normalized


def project_text(title: str, description: str, required_skills: list[str]) -> str:
    return normalize_text(
        f"Title: {title}. Description: {description}. Required skills: {', '.join(required_skills)}"
    )


def interest_text(description: str, skills: list[str]) -> str:
    return normalize_text(f"Research interests: {description}. Skills: {', '.join(skills)}")


def validate_embedding(values) -> list[float]:
    try:
        if hasattr(values, "tolist"):
            values = values.tolist()
        vector = [float(value) for value in values]
    except (TypeError, ValueError, OverflowError) as exc:
        raise EmbeddingUnavailableError("Embedding model returned an invalid vector") from exc
    if len(vector) != EMBEDDING_DIMENSION:
        raise EmbeddingUnavailableError(
            f"Embedding model returned {len(vector)} dimensions; expected {EMBEDDING_DIMENSION}"
        )
    if not all(math.isfinite(value) for value in vector):
        raise EmbeddingUnavailableError("Embedding model returned non-finite values")
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 1e-12:
        raise EmbeddingUnavailableError("Embedding model returned a zero vector")
    return [value / norm for value in vector]


class SentenceTransformerEmbeddingProvider:
    """Loads all-MiniLM-L6-v2 on first use and reuses it for the process."""

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self._model_lock = threading.Lock()

    def _create_model(self):
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(self.model_name, device="cpu")

    def _load_model(self):
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    try:
                        self._model = self._create_model()
                    except Exception as exc:
                        raise EmbeddingUnavailableError(
                            "Embedding model could not be initialized"
                        ) from exc
        return self._model

    def embed(self, text: str) -> list[float]:
        normalized = normalize_text(text)
        model = self._load_model()
        try:
            values = model.encode(
                normalized,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        except Exception as exc:
            raise EmbeddingUnavailableError("Embedding model could not encode the text") from exc
        return validate_embedding(values)


embedding_provider: EmbeddingProvider = SentenceTransformerEmbeddingProvider()


def generate_embedding(text: str) -> list[float]:
    """Use the process-wide provider; kept as the injection point for tests."""
    return validate_embedding(embedding_provider.embed(normalize_text(text)))
