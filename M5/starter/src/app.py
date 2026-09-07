"""API minimale M5 : santé, attribution de version et métriques techniques."""

from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response

from .versioning import load_json, validate_release


DEFAULT_REFERENCE = (
    Path(__file__).resolve().parents[3]
    / "data_pack/2026-S1/reference_runs/m4_for_m5/release_manifest.json"
)
app = FastAPI(title="DiagOps M5 starter", version="1.0.0")


def reference_manifest() -> Path:
    configured = os.environ.get("DIAGOPS_REFERENCE_MANIFEST")
    return Path(configured) if configured else DEFAULT_REFERENCE


def fault_file() -> Path:
    configured = os.environ.get("DIAGOPS_FAULT_FILE")
    return Path(configured) if configured else Path("artifacts/runtime/faults.json")


def active_fault() -> dict:
    path = fault_file()
    return load_json(path) if path.is_file() else {}


def current_release() -> dict:
    release = load_json(reference_manifest())
    validate_release(release)
    return release


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    fault = active_fault()
    delay_ms = min(int(fault.get("readiness_delay_ms", 0)), 2000)
    if delay_ms:
        time.sleep(delay_ms / 1000)
    if fault.get("dependency_available") is False or fault.get("index_valid") is False:
        raise HTTPException(status_code=503, detail="Incident de laboratoire actif")
    if fault.get("release_valid") is False:
        raise HTTPException(status_code=503, detail="Configuration de release incompatible")
    try:
        release = current_release()
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ready", "release_id": str(release["release_id"])}


@app.get("/version")
def version() -> dict:
    try:
        return current_release()
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/metrics")
def metrics() -> Response:
    fault = active_fault()
    try:
        current_release()
        ready_value = 1
    except (OSError, ValueError):
        ready_value = 0
    if fault.get("release_valid") is False:
        ready_value = 0
    dependency_up = int(fault.get("dependency_available", True))
    index_valid = int(fault.get("index_valid", True))
    citation_resolvable_rate = float(fault.get("citation_resolvable_rate", 1.0))
    correct_abstention_rate = float(fault.get("correct_abstention_rate", 1.0))
    expected_document_hit_at_3 = float(fault.get("expected_document_hit_at_3", 1.0))
    body = (
        "# HELP diagops_ready Whether the reference release is valid.\n"
        "# TYPE diagops_ready gauge\n"
        f"diagops_ready {ready_value}\n"
        "# HELP diagops_dependency_up Whether the generation dependency is available.\n"
        "# TYPE diagops_dependency_up gauge\n"
        f"diagops_dependency_up {dependency_up}\n"
        "# HELP diagops_index_valid Whether the active index passed integrity checks.\n"
        "# TYPE diagops_index_valid gauge\n"
        f"diagops_index_valid {index_valid}\n"
        "# HELP diagops_citation_resolvable_rate Share of answer citations resolving to an indexed document.\n"
        "# TYPE diagops_citation_resolvable_rate gauge\n"
        f"diagops_citation_resolvable_rate {citation_resolvable_rate}\n"
        "# HELP diagops_correct_abstention_rate Share of unsupported questions correctly refused.\n"
        "# TYPE diagops_correct_abstention_rate gauge\n"
        f"diagops_correct_abstention_rate {correct_abstention_rate}\n"
        "# HELP diagops_expected_document_hit_at_3 Share of questions whose expected document ranks in the top 3.\n"
        "# TYPE diagops_expected_document_hit_at_3 gauge\n"
        f"diagops_expected_document_hit_at_3 {expected_document_hit_at_3}\n"
    )
    return Response(content=body, media_type="text/plain; version=0.0.4")
