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
