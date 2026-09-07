from pathlib import Path

from src.grounded_answer import validate_citations
from src.io_contracts import load_manifest, load_questions
from src.rag_answers import CALIBRATION_ANSWERS

DATA_PACK = Path(__file__).resolve().parents[3] / "data_pack" / "2026-S1"
MANIFEST = DATA_PACK / "knowledge" / "manifest.csv"
DOCUMENTS = DATA_PACK / "knowledge" / "documents"
QUESTIONS = DATA_PACK / "rag_eval" / "questions.jsonl"


def _admissible_ids() -> set[str]:
    manifest = load_manifest(MANIFEST, DOCUMENTS)
    return {row["document_id"] for row in manifest if row["status"] == "active"}


def test_every_calibration_question_has_a_composed_answer():
    questions = load_questions(QUESTIONS)
    calibration_ids = {q["eval_id"] for q in questions if q["split"] == "calibration"}
    assert calibration_ids == set(CALIBRATION_ANSWERS)


def test_no_answer_cites_an_inadmissible_or_superseded_document():
    admissible = _admissible_ids()
    for eval_id, answer in CALIBRATION_ANSWERS.items():
        errors = validate_citations(answer, admissible)
        assert errors == [], f"{eval_id}: {errors}"


def test_abstained_answers_carry_no_citation():
    for eval_id, answer in CALIBRATION_ANSWERS.items():
        if answer.abstained:
            assert answer.citations == (), eval_id


def test_answered_questions_cite_at_least_one_document():
    for eval_id, answer in CALIBRATION_ANSWERS.items():
        if not answer.abstained:
            assert len(answer.citations) >= 1, eval_id


def test_unanswerable_questions_are_abstained():
    questions = {q["eval_id"]: q for q in load_questions(QUESTIONS)}
    for eval_id, answer in CALIBRATION_ANSWERS.items():
        expected_abstain = not questions[eval_id]["answerable"]
        assert answer.abstained == expected_abstain, eval_id
