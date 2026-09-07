"""Validation locale du contrat de citation et d’abstention."""

from __future__ import annotations

from .contracts import Citation, GroundedAnswer


def abstain(reason: str) -> GroundedAnswer:
    return GroundedAnswer(answer=reason, abstained=True)


def validate_citations(
    answer: GroundedAnswer, admissible_document_ids: set[str]
) -> list[str]:
    errors: list[str] = []
    if answer.abstained and answer.citations:
        errors.append("Une abstention ne doit pas fabriquer de citation.")
    if not answer.abstained and not answer.citations:
        errors.append("Une réponse documentaire doit citer au moins une source.")
    for citation in answer.citations:
        if citation.document_id not in admissible_document_ids:
            errors.append(f"Citation inadmissible : {citation.document_id}")
        if not citation.excerpt.strip():
            errors.append(f"Extrait vide : {citation.document_id}")
    return errors


__all__ = ["Citation", "GroundedAnswer", "abstain", "validate_citations"]
