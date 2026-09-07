from src.retrieval import admissible, rank_lexical


def test_lexical_baseline_returns_matching_document():
    documents = [
        {"document_id": "A", "text": "pression vapeur et unité bar"},
        {"document_id": "B", "text": "consignation électrique"},
    ]
    assert rank_lexical("pression en bar", documents, top_k=1)[0]["document_id"] == "A"


def test_superseded_document_is_not_admissible():
    metadata = {
        "status": "superseded",
        "allowed_roles": "technicien;auditeur",
    }
    assert admissible(metadata, "technicien") is False


def test_role_is_enforced():
    metadata = {"status": "active", "allowed_roles": "superviseur;auditeur"}
    assert admissible(metadata, "public") is False
