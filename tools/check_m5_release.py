#!/usr/bin/env python3
"""Vérifie le paquet apprenant M5 et, en option, le kit formateur."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "M5"
REFERENCE = ROOT / "data_pack" / "2026-S1" / "reference_runs" / "m4_for_m5"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    require(isinstance(value, dict), f"Objet JSON attendu : {path.relative_to(ROOT)}")
    return value


def verify_module_documents() -> dict[str, int]:
    required = [
        MODULE / "module_5_synthese.md",
        MODULE / "brief1_module5.md",
        MODULE / "brief1_module5_online.md",
        MODULE / "brief2_module5.md",
        MODULE / "acquis_m5.md",
        MODULE / "RESOURCES.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    require(not missing, f"Documents M5 absents : {missing}")
    synthesis = (MODULE / "module_5_synthese.md").read_text(encoding="utf-8")
    for marker in ("40 h", "C6", "C8", "C9", "14 h", "6 h", "20 h"):
        require(marker in synthesis, f"Synthèse M5 : marqueur absent {marker!r}")
    return {"module_documents": len(required)}


def verify_starter() -> dict[str, int]:
    required = [
        "README.md", "requirements.lock", "pyproject.toml",
        "configs/gates.json", "configs/release.example.json",
        "deploy/Dockerfile", "deploy/compose.yaml", "deploy/prometheus.yml",
        "src/app.py", "src/versioning.py",
        "pipelines/build_index.py", "pipelines/evaluate_release.py",
        "pipelines/promote_release.py", "pipelines/rollback_release.py",
        "tests/test_build_index.py", "tests/test_health.py",
        "tests/test_release_gate.py", "tests/test_rollback.py",
        "monitoring/metrics.md", "docs/contrat_versions.md", "docs/runbook.md",
        "docs/rapport_rollback.md", "game_day/plan.md", "game_day/timeline.md",
        "game_day/post_incident.md", "game_day/remediation.md", "journal_bord.md",
    ]
    missing = [item for item in required if not (MODULE / "starter" / item).is_file()]
    require(not missing, f"Starter M5 incomplet : {missing}")
    gates = load_json(MODULE / "starter" / "configs" / "gates.json")
    require(gates["minimum_document_count"] == 7, "Gate corpus : sept documents actifs attendus")
    return {"starter_files": len(required)}


def verify_checksums() -> int:
    checksum_file = REFERENCE / "checksums.sha256"
    require(checksum_file.is_file(), "Checksums de la référence M4 absents")
    checked = 0
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        target = (REFERENCE / relative).resolve()
        require(REFERENCE.resolve() in target.parents, f"Chemin de checksum hors référence : {relative}")
        require(target.is_file(), f"Fichier référencé absent : {relative}")
        require(sha256(target) == expected, f"Checksum invalide : {relative}")
        checked += 1
    return checked


def verify_data_pack_checksums() -> int:
    data_pack = ROOT / "data_pack"
    checksum_file = data_pack / "checksums.sha256"
    require(checksum_file.is_file(), "Checksums globaux du data pack absents")
    checked = 0
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        target = (data_pack / relative).resolve()
        require(data_pack.resolve() in target.parents, f"Chemin hors data pack : {relative}")
        require(target.is_file(), f"Fichier du data pack absent : {relative}")
        require(sha256(target) == expected, f"Checksum global invalide : {relative}")
        checked += 1
    required_reference = {
        str(path.relative_to(data_pack))
        for path in REFERENCE.rglob("*")
        if path.is_file()
    }
    listed = {
        line.split("  ", 1)[1]
        for line in checksum_file.read_text(encoding="utf-8").splitlines()
    }
    actual = {
        str(path.relative_to(data_pack))
        for path in data_pack.rglob("*")
        if path.is_file()
        and path != checksum_file
        and path.name != ".DS_Store"
    }
    require(listed == actual, "Inventaire des checksums globaux incomplet ou obsolète")
    require(required_reference <= listed, "Référence M4 incomplète dans les checksums globaux")
    return checked


def verify_reference() -> dict[str, int | float]:
    release = load_json(REFERENCE / "release_manifest.json")
    require(release["release_id"] == "diagops-m4-reference-r1", "Identité de release M4 invalide")
    require(release["deployment_scope"] == "pedagogical_preproduction_only", "Périmètre de déploiement absent")
    required_fields = {
        "code_version", "model_version", "corpus_version", "index_version",
        "prompt_version", "evaluation_version",
    }
    require(required_fields <= set(release), "Versions liées incomplètes")
    for name, component in release["components"].items():
        target = (REFERENCE / component["path"]).resolve()
        require(target.is_file(), f"Composant absent : {name}")
        require(sha256(target) == component["sha256"], f"Composant altéré : {name}")

    with (ROOT / "data_pack" / "2026-S1" / "knowledge" / "manifest.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        active_ids = {row["document_id"] for row in csv.DictReader(handle) if row["status"] == "active"}
    index = load_json(REFERENCE / "index" / "index_manifest.json")
    indexed_ids = {row["document_id"] for row in index["documents"]}
    require(indexed_ids == active_ids, "L'index de référence ne correspond pas au corpus actif")
    require(index["document_count"] == 7, "Sept documents actifs attendus")

    predictions = [
        json.loads(line)
        for line in (REFERENCE / "evaluation" / "predictions_calibration.jsonl")
        .read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    require(len(predictions) == 12, "Douze prédictions de calibration attendues")
    require(all(row["eval_id"].startswith("RAG-CAL-") for row in predictions), "Split test exposé")
    metrics = load_json(REFERENCE / "evaluation" / "metrics_calibration.json")
    require(metrics["test_split_used"] is False, "Le split test ne doit pas être utilisé")
    require(metrics["expected_document_hit_at_3"] >= 0.8, "Baseline retrieval insuffisante")
    require(metrics["citation_resolvable_rate"] == 1.0, "Citations non résolubles")
    require(metrics["correct_abstention_rate"] == 1.0, "Abstentions de référence incorrectes")
    checksums = verify_checksums()
    data_pack_checksums = verify_data_pack_checksums()

    manifest = (ROOT / "data_pack" / "MANIFEST.yaml").read_text(encoding="utf-8")
    block = manifest.split('path: "2026-S1/reference_runs/m4_for_m5/"', 1)[1].split("\n\n", 1)[0]
    require("delivery_status: ready_for_distribution" in block, "Référence M4 non publiable")
    return {
        "reference_files": checksums,
        "data_pack_files": data_pack_checksums,
        "active_documents": len(active_ids),
        "calibration_questions": len(predictions),
        "retrieval_hit_at_3": metrics["expected_document_hit_at_3"],
    }


def verify_trainer() -> dict[str, int]:
    root = ROOT / "_conception" / "M5"
    required = [root / "README.md", root / "objectives.json", root / "inject_incident.py"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    require(not missing, f"Kit formateur M5 absent : {missing}")
    objectives = load_json(root / "objectives.json")
    require(objectives["maximum_restore_seconds"] <= 600, "Objectif de restauration trop permissif")
    scenarios = sorted((root / "scenarios").glob("*.json"))
    require(len(scenarios) >= 3, "Trois scénarios formateur au minimum sont requis")
    for path in scenarios:
        scenario = load_json(path)
        require(scenario["scenario_id"] == path.stem, f"Identité de scénario invalide : {path.name}")
        require(bool(scenario["expected_signals"]), f"Signaux attendus absents : {path.name}")
    return {"trainer_scenarios": len(scenarios)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trainer", action="store_true")
    args = parser.parse_args()
    result: dict[str, int | float | str] = {"status": "ready"}
    result.update(verify_module_documents())
    result.update(verify_starter())
    result.update(verify_reference())
    if args.trainer:
        result.update(verify_trainer())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
