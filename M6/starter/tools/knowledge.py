"""Outil `search_knowledge` : recherche documentaire bornée, en lecture seule."""

from __future__ import annotations

import re
from collections import Counter

from . import ToolResult, knowledge_documents


SPEC = {
    "name": "search_knowledge",
    "purpose": "Retrouver les passages de procédure ou de politique qui fondent une réponse.",
    "arguments": [
        {
            "name": "query",
            "type": "string",
            "required": True,
            "min_length": 3,
            "max_length": 200,
            "description": "question ou termes de recherche, en clair",
        },
        {
            "name": "top_k",
            "type": "integer",
            "required": False,
            "minimum": 1,
            "maximum": 3,
            "default": 3,
            "description": "nombre de documents retournés",
        },
    ],
    "result_fields": ["document_id", "title", "revision", "excerpt", "score"],
    "source_of_truth": "data_pack/2026-S1/knowledge/ (documents actifs du manifeste)",
    "authorized_roles": ["technicien", "superviseur", "auditeur", "public"],
    "timeout_ms": 1500,
    "max_results": 3,
    "sensitive_data": "extraits de documents internes ou restreints, filtrés par rôle",
    "errors": ["checksum invalide", "corpus indisponible"],
    "degraded_mode": "résultat vide et motif explicite ; la réponse doit alors refuser",
    "side_effects": False,
}

TOKEN = re.compile(r"[\wÀ-ÿ-]+", re.UNICODE)
EXCERPT_WINDOW = 240


def _tokens(text: str) -> list[str]:
    return [item.lower() for item in TOKEN.findall(text)]


def _score(query: str, text: str) -> float:
    query_counts = Counter(_tokens(query))
    text_counts = Counter(_tokens(text))
    return float(sum(min(count, text_counts[token]) for token, count in query_counts.items()))


def _excerpt(query: str, text: str) -> str:
    terms = [token for token in _tokens(query) if len(token) > 3]
    lowered = text.lower()
    position = next((lowered.find(term) for term in terms if lowered.find(term) >= 0), -1)
    if position < 0:
        return text[:EXCERPT_WINDOW].strip()
    start = max(0, position - EXCERPT_WINDOW // 3)
    return text[start:start + EXCERPT_WINDOW].strip()


def run(arguments: dict, *, role: str) -> ToolResult:
    query = arguments["query"]
    top_k = int(arguments.get("top_k", SPEC["max_results"]))
    documents = [
        document for document in knowledge_documents()
        if role in document["allowed_roles"]
    ]
    scored = [
        (document, _score(query, document["text"])) for document in documents
    ]
    ranked = sorted(
        (item for item in scored if item[1] > 0),
        key=lambda item: (item[1], item[0]["document_id"]),
        reverse=True,
    )
    selected = ranked[:top_k]
    rows = tuple(
        {
            "document_id": document["document_id"],
            "title": document["title"],
            "revision": document["revision"],
            "excerpt": _excerpt(query, document["text"]),
            "score": score,
        }
        for document, score in selected
    )
    return ToolResult(
        tool=SPEC["name"],
        rows=rows,
        source="knowledge/manifest.csv",
        truncated=len(ranked) > len(selected),
        reason="" if rows else "aucun document actif admissible pour ce rôle et cette requête",
    )
