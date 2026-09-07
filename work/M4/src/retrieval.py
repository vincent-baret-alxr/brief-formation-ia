"""Baseline lexicale transparente et contrat d’admission documentaire."""

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
        key=lambda document: (
            lexical_score(query, document["text"]), document["document_id"]
        ),
        reverse=True,
    )
    return [item for item in ranked if lexical_score(query, item["text"]) > 0][:top_k]


def admissible(metadata: dict[str, str], role: str) -> bool:
    roles = {item for item in metadata["allowed_roles"].split(";") if item}
    return metadata["status"] == "active" and role in roles
