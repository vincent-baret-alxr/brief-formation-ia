"""Agent à une décision, sans boucle ni effet externe."""

from __future__ import annotations

from .contracts import AgentDecision


ALLOWED_ACTIONS = frozenset({"answer_without_tool", "search_knowledge", "abstain"})


def validate_decision(decision: AgentDecision) -> None:
    if decision.action not in ALLOWED_ACTIONS:
        raise ValueError(f"Action interdite : {decision.action}")
    if decision.action == "search_knowledge" and not decision.retrieval_query:
        raise ValueError("Une recherche exige une requête explicite.")
    if decision.action != "search_knowledge" and decision.retrieval_query:
        raise ValueError("La requête est réservée à search_knowledge.")


def decide(*, needs_documents: bool, answerable_without_tool: bool, query: str) -> AgentDecision:
    if answerable_without_tool:
        decision = AgentDecision("answer_without_tool", "Réponse contractuelle directe")
    elif needs_documents and query.strip():
        decision = AgentDecision("search_knowledge", "Preuve documentaire requise", query.strip())
    else:
        decision = AgentDecision("abstain", "Aucune preuve admissible disponible")
    validate_decision(decision)
    return decision
