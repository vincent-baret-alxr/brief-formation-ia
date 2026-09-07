from src.contracts import Citation, GroundedAnswer
from src.grounded_answer import validate_citations


def test_grounded_answer_accepts_a_resolvable_citation():
    answer = GroundedAnswer(
        answer="La procédure active exige une vérification croisée.",
        citations=(Citation("DOC-LOTO-002", "une seconde personne habilitée"),),
    )
    assert validate_citations(answer, {"DOC-LOTO-002"}) == []


def test_unknown_document_is_rejected():
    answer = GroundedAnswer(
        answer="Réponse",
        citations=(Citation("DOC-INEXISTANT", "extrait"),),
    )
    assert validate_citations(answer, {"DOC-LOTO-002"})


def test_documentary_answer_without_citation_is_rejected():
    assert validate_citations(GroundedAnswer(answer="Réponse"), set())
