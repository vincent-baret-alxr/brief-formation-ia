"""Baseline lexicale figée transmise de M4 à M5."""

from __future__ import annotations

import re
from collections import Counter


TOKEN = re.compile(r"[\wÀ-ÿ-]+", re.UNICODE)


def tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN.findall(text)]


def lexical_score(query: str, text: str) -> float:
    query_counts = Counter(tokens(query))
    text_counts = Counter(tokens(text))
    return float(sum(min(count, text_counts[token]) for token, count in query_counts.items()))


def rank_lexical(query: str, documents: list[dict], top_k: int = 3) -> list[dict]:
    ranked = sorted(
        documents,
        key=lambda document: (lexical_score(query, document["text"]), document["document_id"]),
        reverse=True,
    )
    return [item for item in ranked if lexical_score(query, item["text"]) > 0][:top_k]
