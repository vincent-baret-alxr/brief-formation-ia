"""Retrieval vectoriel documenté, entièrement local.

Modèle choisi : `sentence-transformers/all-MiniLM-L6-v2`. Justification
(voir aussi `docs/benchmark_retrieval.md`) :

- petit (≈ 80 Mo), rapide en CPU, adapté à un corpus de 8 documents courts ;
- multi-usage général, pas d'API externe ni de clé à gérer : reproductible
  hors-ligne une fois téléchargé, contrairement à un modèle propriétaire
  servi par API ;
- alternative écartée : TF-IDF pur (`sklearn`) — plus simple et sans
  téléchargement, mais moins robuste aux reformulations qui ne partagent pas
  le vocabulaire exact des documents (cas fréquent dans les 12 questions de
  calibration).
"""

from __future__ import annotations

import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"

_model_cache: dict[str, object] = {}


def get_model(model_name: str = MODEL_NAME):
    if model_name not in _model_cache:
        from sentence_transformers import SentenceTransformer

        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]


def build_index(documents: list[dict], model_name: str = MODEL_NAME) -> np.ndarray:
    """Encode chaque document (normalisé) : le produit scalaire donne ensuite un cosinus."""
    model = get_model(model_name)
    texts = [document["text"] for document in documents]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(embeddings)


def rank_vector(
    query: str,
    documents: list[dict],
    embeddings: np.ndarray,
    top_k: int = 3,
    model_name: str = MODEL_NAME,
) -> list[dict]:
    model = get_model(model_name)
    query_embedding = model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
    scores = embeddings @ query_embedding
    order = np.argsort(-scores)
    ranked = [{**documents[i], "score": float(scores[i])} for i in order]
    return [item for item in ranked if item["score"] > 0][:top_k]


def rank_hybrid(
    query: str,
    documents: list[dict],
    embeddings: np.ndarray,
    top_k: int = 3,
    lexical_weight: float = 0.5,
    model_name: str = MODEL_NAME,
) -> list[dict]:
    """Fusion par score : moyenne pondérée du score lexical et du cosinus vectoriel, chacun normalisé sur [0, 1]."""
    from .retrieval import lexical_score

    lexical_raw = np.array([lexical_score(query, document["text"]) for document in documents])
    lexical_norm = lexical_raw / lexical_raw.max() if lexical_raw.max() > 0 else lexical_raw

    model = get_model(model_name)
    query_embedding = model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
    vector_raw = embeddings @ query_embedding
    vector_norm = (vector_raw - vector_raw.min()) / (vector_raw.max() - vector_raw.min() + 1e-9)

    combined = lexical_weight * lexical_norm + (1 - lexical_weight) * vector_norm
    order = np.argsort(-combined)
    ranked = [{**documents[i], "score": float(combined[i])} for i in order]
    return [item for item in ranked if item["score"] > 0][:top_k]
