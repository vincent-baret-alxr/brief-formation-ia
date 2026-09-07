import pytest

from src.bounded_agent import ALLOWED_ACTIONS, decide, validate_decision
from src.contracts import AgentDecision


def test_agent_exposes_exactly_three_actions():
    assert ALLOWED_ACTIONS == {
        "answer_without_tool", "search_knowledge", "abstain"
    }


def test_search_requires_an_explicit_query():
    with pytest.raises(ValueError):
        validate_decision(AgentDecision("search_knowledge", "raison", ""))


def test_no_evidence_leads_to_abstention():
    decision = decide(
        needs_documents=False, answerable_without_tool=False, query=""
    )
    assert decision.action == "abstain"
