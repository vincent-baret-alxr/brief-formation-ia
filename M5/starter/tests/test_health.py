import json

from fastapi.testclient import TestClient

from src.app import app


def test_liveness_is_independent_of_dependencies() -> None:
    response = TestClient(app).get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "live"}


def test_reference_release_is_ready(monkeypatch) -> None:
    monkeypatch.delenv("DIAGOPS_REFERENCE_MANIFEST", raising=False)
    monkeypatch.delenv("DIAGOPS_FAULT_FILE", raising=False)
    response = TestClient(app).get("/health/ready")
    assert response.status_code == 200
    assert response.json()["release_id"] == "diagops-m4-reference-r1"


def test_readiness_reports_missing_reference(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DIAGOPS_REFERENCE_MANIFEST", str(tmp_path / "missing.json"))
    response = TestClient(app).get("/health/ready")
    assert response.status_code == 503


def test_quality_plane_degrades_while_service_plane_stays_green(monkeypatch, tmp_path) -> None:
    fault = tmp_path / "faults.json"
    fault.write_text(
        json.dumps(
            {
                "dependency_available": True,
                "index_valid": True,
                "readiness_delay_ms": 0,
                "citation_resolvable_rate": 0.5,
                "correct_abstention_rate": 0.6,
                "expected_document_hit_at_3": 0.7,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("DIAGOPS_REFERENCE_MANIFEST", raising=False)
    monkeypatch.setenv("DIAGOPS_FAULT_FILE", str(fault))
    client = TestClient(app)
    assert client.get("/health/ready").status_code == 200
    body = client.get("/metrics").text
    assert "diagops_ready 1" in body
    assert "diagops_index_valid 1" in body
    assert "diagops_citation_resolvable_rate 0.5" in body
    assert "diagops_correct_abstention_rate 0.6" in body
    assert "diagops_expected_document_hit_at_3 0.7" in body


def test_incompatible_release_configuration_blocks_readiness(monkeypatch, tmp_path) -> None:
    fault = tmp_path / "faults.json"
    fault.write_text(
        json.dumps(
            {
                "dependency_available": True,
                "index_valid": True,
                "readiness_delay_ms": 0,
                "release_valid": False,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("DIAGOPS_REFERENCE_MANIFEST", raising=False)
    monkeypatch.setenv("DIAGOPS_FAULT_FILE", str(fault))
    client = TestClient(app)
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 503
    body = client.get("/metrics").text
    assert "diagops_ready 0" in body
    assert "diagops_dependency_up 1" in body
    assert "diagops_index_valid 1" in body
