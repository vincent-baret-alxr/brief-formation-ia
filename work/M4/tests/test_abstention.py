from src.contracts import Citation
from src.grounded_answer import abstain, validate_citations


def test_abstention_has_no_citation():
    answer = abstain("Preuve documentaire insuffisante")
    assert answer.abstained is True
    assert answer.citations == ()
    assert validate_citations(answer, set()) == []


def test_abstention_with_a_fabricated_citation_is_rejected():
    answer = abstain("Preuve insuffisante")
    forged = type(answer)(
        answer=answer.answer,
        abstained=True,
        citations=(Citation("DOC-FAUX", "extrait"),),
    )
    assert validate_citations(forged, set())
