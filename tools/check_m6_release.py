#!/usr/bin/env python3
"""Vérifie le paquet apprenant M6 et, en option, le kit formateur."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "M6"
STARTER = MODULE / "starter"
REFERENCE = ROOT / "data_pack" / "2026-S1" / "reference_runs" / "m5_for_m6"
PERIOD = ROOT / "data_pack" / "2027-S1"

REQUIRED_CATEGORIES = {
    "nominal_document", "nominal_equipment", "nominal_events", "nominal_history",
    "nominal_report", "multi_step", "useless_tool", "unknown_id", "invalid_argument",
    "empty_result", "unavailable_tool", "timeout", "injection_question",
    "role_restriction", "out_of_scope", "contradictory_sources",
}
EXPECTED_TOOLS = {
    "search_knowledge", "get_equipment", "list_events",
    "get_maintenance_history", "diagnose_report",
}


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


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def verify_module_documents() -> dict[str, int]:
    required = [
        MODULE / "module_6_synthese.md",
        MODULE / "brief1_module6.md",
        MODULE / "brief1_module6_online.md",
        MODULE / "brief2_module6.md",
        MODULE / "acquis_m6.md",
        MODULE / "RESOURCES.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    require(not missing, f"Documents M6 absents : {missing}")
    synthesis = (MODULE / "module_6_synthese.md").read_text(encoding="utf-8")
    for marker in ("40 h", "C5", "C8", "C9", "14 h", "6 h", "20 h"):
        require(marker in synthesis, f"Synthèse M6 : marqueur absent {marker!r}")
    return {"module_documents": len(required)}


def verify_starter_files() -> dict[str, int]:
    required = [
        "README.md", "requirements.lock", "pyproject.toml", "journal_bord.md",
        "agent/policy.yaml", "agent/registry.py", "agent/runner.py",
        "tools/__init__.py", "tools/knowledge.py", "tools/equipment.py",
        "tools/events.py", "tools/maintenance.py", "tools/diagnose.py",
        "eval/scenarios.jsonl", "eval/run_agent_eval.py",
        "feedback/qualify_feedback.py",
        "tests/test_tool_contracts.py", "tests/test_policy_bounds.py",
        "tests/test_no_side_effects.py",
        "docs/registre_outils.md", "docs/qualification_feedback.md",
        "adversarial/campaign.jsonl", "adversarial/invariants.md",
        "adversarial/report.md", "adversarial/remediation.md",
    ]
    missing = [item for item in required if not (STARTER / item).is_file()]
    require(not missing, f"Starter M6 incomplet : {missing}")
    return {"starter_files": len(required)}


def verify_tool_contracts() -> dict[str, int]:
    sys.path.insert(0, str(STARTER))
    try:
        from agent.registry import default_registry  # noqa: PLC0415
        from agent.runner import load_policy  # noqa: PLC0415

        registry = default_registry()
        require(set(registry.names()) == EXPECTED_TOOLS, "Les cinq outils M6 ne sont pas enregistrés")
        require(registry.frozen, "Le registre distribué n'est pas gelé")
        for name in registry.names():
            spec = registry.spec(name)
            require(spec.side_effects is False, f"Outil à effet externe : {name}")
            require(spec.timeout_ms > 0 and spec.max_results > 0, f"Bornes absentes : {name}")
            require(bool(spec.degraded_mode and spec.errors), f"Mode dégradé ou erreurs absents : {name}")
        policy = load_policy(STARTER / "agent" / "policy.yaml")
        require(policy.allow_dynamic_tools is False, "La politique autorise l'ajout dynamique d'outils")
        require(policy.allowlist == EXPECTED_TOOLS, "Liste blanche distribuée incohérente")
        require(policy.budget.max_steps <= 8, "Budget d'étapes trop permissif")
        require("raw_arguments" in policy.trace_forbidden_fields, "Les arguments bruts ne sont pas interdits de trace")
    finally:
        sys.path.remove(str(STARTER))
    return {"registered_tools": len(EXPECTED_TOOLS)}


def verify_scenarios() -> dict[str, int]:
    scenarios = read_jsonl(STARTER / "eval" / "scenarios.jsonl")
    require(len(scenarios) >= 18, "Jeu de scénarios trop court")
    identifiers = [row["scenario_id"] for row in scenarios]
    require(len(set(identifiers)) == len(identifiers), "Identifiants de scénario dupliqués")
    categories = {row["category"] for row in scenarios}
    missing = sorted(REQUIRED_CATEGORIES - categories)
    require(not missing, f"Catégories de scénarios absentes : {missing}")
    for row in scenarios:
        require(row["expectation"] in {"answer", "refuse"}, f"Attente invalide : {row['scenario_id']}")
        unknown = set(row["expected_tools"]) - EXPECTED_TOOLS
        require(not unknown, f"Outil inconnu dans {row['scenario_id']} : {sorted(unknown)}")

    campaign = read_jsonl(STARTER / "adversarial" / "campaign.jsonl")
    require(len(campaign) >= 6, "Campagne adversariale trop courte")
    require(all(row.get("invariant") for row in campaign), "Cas adverse sans invariant associé")
    invariants = (STARTER / "adversarial" / "invariants.md").read_text(encoding="utf-8")
    for identifier in ("INV-01", "INV-02", "INV-03", "INV-04", "INV-05", "INV-06", "INV-07"):
        require(identifier in invariants, f"Invariant absent du catalogue : {identifier}")
    return {"scenarios": len(scenarios), "adversarial_cases": len(campaign)}


def verify_period_2027() -> dict[str, int]:
    reports_path = PERIOD / "reports" / "reports.jsonl"
    feedback_path = PERIOD / "feedback" / "feedback.csv"
    require(reports_path.is_file(), "Rapports 2027-S1 absents")
    require(feedback_path.is_file(), "Feedback 2027-S1 absent")

    reports = read_jsonl(reports_path)
    require(len(reports) == 60, "Soixante rapports 2027-S1 attendus")
    require(all(row["period"] == "2027-S1" for row in reports), "Période incohérente dans les rapports")
    identifiers = {row["report_id"] for row in reports}
    require(len(identifiers) == len(reports), "report_id dupliqué en 2027-S1")

    with feedback_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        feedback = list(reader)
    expected_fields = {
        "feedback_id", "report_id", "event_id", "timestamp", "user_decision",
        "model_helpfulness", "comment", "submitted_by_id", "submitted_by_role",
        "batch", "period",
    }
    require(fields == expected_fields, f"Colonnes de feedback inattendues : {sorted(fields ^ expected_fields)}")
    require("expected_class" not in fields, "La clé de qualification ne doit pas être distribuée")
    require(len(feedback) == 124, "Cent vingt-quatre retours attendus")
    batches = {row["batch"] for row in feedback}
    require(batches == {"b1", "b2"}, "Les deux lots de feedback sont attendus")
    require(
        any(row["report_id"] not in identifiers for row in feedback),
        "Le lot doit contenir au moins un retour non relié à un rapport connu",
    )
    return {"reports_2027": len(reports), "feedback_rows": len(feedback)}


def verify_reference() -> dict[str, int | float]:
    release = load_json(REFERENCE / "release_manifest.json")
    require(release["release_id"] == "diagops-m5-reference-r1", "Identité de release M5 invalide")
    require(release["deployment_scope"] == "pedagogical_preproduction_only", "Périmètre de déploiement absent")
    require(release["gate_status"] == "passed", "La référence M5 ne passe pas son gate")
    require(release["supersedes_release_id"] == "diagops-m4-reference-r1", "Chaînage de release absent")
    for name, component in release["components"].items():
        target = (REFERENCE / component["path"]).resolve()
        require(target.is_file(), f"Composant absent : {name}")
        require(sha256(target) == component["sha256"], f"Composant altéré : {name}")

    with (ROOT / "data_pack" / "2026-S1" / "knowledge" / "manifest.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        active_ids = {row["document_id"] for row in csv.DictReader(handle) if row["status"] == "active"}
    index = load_json(REFERENCE / "index" / "index_manifest.json")
    require({row["document_id"] for row in index["documents"]} == active_ids,
            "L'index de référence ne correspond pas au corpus actif")

    predictions = read_jsonl(REFERENCE / "evaluation" / "predictions_calibration.jsonl")
    require(len(predictions) == 12, "Douze prédictions de calibration attendues")
    require(all(row["eval_id"].startswith("RAG-CAL-") for row in predictions), "Split test exposé")
    metrics = load_json(REFERENCE / "evaluation" / "metrics_calibration.json")
    require(metrics["test_split_used"] is False, "Le split test ne doit pas être utilisé")
    require(metrics["maximum_agent_steps"] == 1, "La référence doit rester à une étape")
    gate = load_json(REFERENCE / "gates" / "gate_report.json")
    require(gate["status"] == "passed", "Rapport de gate en échec")
    require(all(item["passed"] for item in gate["checks"].values()), "Un contrôle de gate est en échec")

    for relative in ("baseline/retrieval.py", "baseline/bounded_agent.py",
                     "operations/runbook.md", "operations/restauration.md",
                     "monitoring/metrics_contract.md", "monitoring/baseline_metrics.json",
                     "veille_diagops/journal.md", "decision_m5.md", "risks.md"):
        require((REFERENCE / relative).is_file(), f"Artefact de continuité absent : {relative}")
    journal = (REFERENCE / "veille_diagops" / "journal.md").read_text(encoding="utf-8")
    require("Entrée M6" in journal, "Le passage de relais réglementaire vers M6 est absent")
    return {
        "reference_files": verify_checksums(),
        "active_documents": len(active_ids),
        "calibration_questions": len(predictions),
        "retrieval_hit_at_3": metrics["expected_document_hit_at_3"],
    }


def verify_checksums() -> int:
    checksum_file = REFERENCE / "checksums.sha256"
    require(checksum_file.is_file(), "Checksums de la référence M5 absents")
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
    listed: dict[str, str] = {}
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        listed[relative] = expected
    actual = {
        str(path.relative_to(data_pack))
        for path in data_pack.rglob("*")
        if path.is_file() and path != checksum_file and path.name != ".DS_Store"
    }
    require(set(listed) == actual, "Inventaire des checksums globaux incomplet ou obsolète")
    for relative, expected in listed.items():
        require(sha256(data_pack / relative) == expected, f"Checksum global invalide : {relative}")
    return len(listed)


def verify_manifest() -> dict[str, str]:
    manifest = (ROOT / "data_pack" / "MANIFEST.yaml").read_text(encoding="utf-8")
    for path in ('2026-S1/reference_runs/m5_for_m6/', '2027-S1/reports/reports.jsonl',
                 '2027-S1/feedback/feedback.csv'):
        block = manifest.split(f'path: "{path}"', 1)[1].split("\n\n", 1)[0]
        require("delivery_status: ready_for_distribution" in block, f"Actif non publiable : {path}")
    parsed = yaml.safe_load(manifest)
    require(parsed["current_release"] == "diagops-2026-S1-m6-v1", "Release courante du pack non mise à jour")
    return {"current_release": parsed["current_release"]}


def verify_trainer() -> dict[str, int]:
    root = ROOT / "_conception" / "M6"
    required = [root / "generate_m6_data.py", root / "feedback_oracle.csv", root / "README.md"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    require(not missing, f"Kit formateur M6 absent : {missing}")
    with (root / "feedback_oracle.csv").open(encoding="utf-8", newline="") as handle:
        oracle = list(csv.DictReader(handle))
    require(len(oracle) == 124, "La clé de qualification doit couvrir tout le lot")
    require(
        not (ROOT / "data_pack" / "2027-S1" / "feedback" / "feedback_oracle.csv").exists(),
        "La clé de qualification ne doit jamais être publiée",
    )
    return {"oracle_rows": len(oracle)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trainer", action="store_true")
    args = parser.parse_args()
    result: dict[str, object] = {"status": "ready"}
    result.update(verify_module_documents())
    result.update(verify_starter_files())
    result.update(verify_tool_contracts())
    result.update(verify_scenarios())
    result.update(verify_period_2027())
    result.update(verify_reference())
    result["data_pack_files"] = verify_data_pack_checksums()
    result.update(verify_manifest())
    if args.trainer:
        result.update(verify_trainer())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
