"""Décision de référence M4 : une action, aucune boucle, aucun effet externe."""

from __future__ import annotations


ALLOWED_ACTIONS = frozenset({"answer_without_tool", "search_knowledge", "abstain"})


def decide(*, needs_documents: bool, answerable_without_tool: bool, query: str) -> dict:
    if answerable_without_tool:
        return {"action": "answer_without_tool", "retrieval_query": None}
    if needs_documents and query.strip():
        return {"action": "search_knowledge", "retrieval_query": query.strip()}
    return {"action": "abstain", "retrieval_query": None}
