"""Contrats minimaux pour les citations et l’agent borné."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


AgentAction = Literal["answer_without_tool", "search_knowledge", "abstain"]


@dataclass(frozen=True)
class Citation:
    document_id: str
    excerpt: str


@dataclass(frozen=True)
class GroundedAnswer:
    answer: str
    citations: tuple[Citation, ...] = field(default_factory=tuple)
    abstained: bool = False
    interpretation: str = ""


@dataclass(frozen=True)
class AgentDecision:
    action: AgentAction
    rationale: str
    retrieval_query: str | None = None
