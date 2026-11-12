import math

import pytest

from app.services.embeddings import (
    EMBEDDING_DIMENSION,
    EmbeddingUnavailableError,
    SentenceTransformerEmbeddingProvider,
    normalize_text,
    validate_embedding,
)


def test_embedding_dimension_normalization_and_text_normalization():
    assert normalize_text("  cafe\n  systems  ") == "cafe systems"
    vector = validate_embedding([2.0] + [0.0] * (EMBEDDING_DIMENSION - 1))
    assert len(vector) == EMBEDDING_DIMENSION
    assert math.isclose(math.sqrt(sum(value * value for value in vector)), 1.0)


@pytest.mark.parametrize("vector", ([1.0], [0.0] * EMBEDDING_DIMENSION, [float("nan")] + [0.0] * (EMBEDDING_DIMENSION - 1)))
def test_invalid_vectors_are_rejected(vector):
    with pytest.raises(EmbeddingUnavailableError):
        validate_embedding(vector)


def test_model_is_lazy_cached_and_encodes_normalized_text(monkeypatch):
    provider = SentenceTransformerEmbeddingProvider()
    calls = {"loads": 0, "encodes": 0}

    class Model:
        def encode(self, text, **kwargs):
            calls["encodes"] += 1
            assert text == "research interests"
            assert kwargs["normalize_embeddings"] is True
            return [1.0] + [0.0] * (EMBEDDING_DIMENSION - 1)

    def load_model():
        calls["loads"] += 1
        return Model()

    monkeypatch.setattr(provider, "_create_model", load_model)
    assert provider._model is None
    assert len(provider.embed("research   interests")) == EMBEDDING_DIMENSION
    assert len(provider.embed("research interests")) == EMBEDDING_DIMENSION
    assert calls == {"loads": 1, "encodes": 2}


def test_model_initialization_failure_is_explicit_and_not_zero_filled(monkeypatch):
    provider = SentenceTransformerEmbeddingProvider()

    def fail_loading():
        raise OSError("offline model cache")

    monkeypatch.setattr(provider, "_create_model", fail_loading)
    with pytest.raises(EmbeddingUnavailableError, match="could not be initialized"):
        provider.embed("meaningful research text")
