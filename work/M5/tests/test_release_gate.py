from pipelines.evaluate_release import evaluate


GATES = {
    "minimum_document_count": 7,
    "minimum_expected_document_hit_at_3": 0.8,
    "minimum_citation_resolvable_rate": 1.0,
    "minimum_correct_abstention_rate": 1.0,
}


def test_gate_passes_reference_quality() -> None:
    index = {"document_count": 7}
    metrics = {
        "expected_document_hit_at_3": 0.9,
        "citation_resolvable_rate": 1.0,
        "correct_abstention_rate": 1.0,
    }
    assert evaluate(index, metrics, GATES)["status"] == "passed"


def test_gate_blocks_retrieval_regression() -> None:
    index = {"document_count": 7}
    metrics = {
        "expected_document_hit_at_3": 0.5,
        "citation_resolvable_rate": 1.0,
        "correct_abstention_rate": 1.0,
    }
    report = evaluate(index, metrics, GATES)
    assert report["status"] == "failed"
    assert report["checks"]["expected_document_hit_at_3"] is False
