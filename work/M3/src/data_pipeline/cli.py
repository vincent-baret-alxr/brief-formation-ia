"""Pipeline multi-source DiagOps M3.

Reprend la préparation de référence M2 (voir ``m2_rules.py`` et
``docs/registre_regles.md`` pour la justification de ce choix), y intègre
``sensor_readings.csv`` (``sensor_rules.py``), rapproche les mesures des
événements et produit une quarantaine et un registre de règles unifiés.

Étapes, dans l'ordre, toutes rejouables depuis les fichiers reçus :

1. préparer équipements, événements, interventions (règles héritées R-*) ;
2. préparer les mesures capteurs (règles nouvelles SEN-*) ;
3. rapprocher mesures et événements sur une fenêtre temporelle documentée ;
4. agréger les mesures rapprochées à un grain équipement × capteur ×
   événement ;
5. écrire les tables préparées, les agrégats, le rapprochement, la
   quarantaine unifiée, le registre de règles et le rapport de validation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from contracts.schemas import (  # noqa: E402
    align_measures_to_events,
    sensor_schema,
    sensor_value_ranges,
)

from . import m2_rules, sensor_rules
from .io import load_sources, source_checksums
from .quarantine import QUARANTINE_COLUMNS, merge_quarantines, quarantine_frame
from .rules import Rule, RuleRegistry
from .timeseries import series_overview

# Fenêtre de rapprochement mesures <-> événements, voir la question 8 de
# docs/diagnostic_multisource.md : 24 h avant le début (couvre 4 relevés au
# pas nominal de 6 h, assez pour une tendance), 6 h après (vérifie la
# continuité des mesures sans absorber l'effet de l'intervention qui suit
# souvent l'événement).
WINDOW_BEFORE_HOURS = 24
WINDOW_AFTER_HOURS = 6

M2_RULE_DESCRIPTIONS: dict[str, tuple[str, str, str]] = {
    # rule_id: (table, description, statut M3)
    "R-EQ-001": ("equipment", "equipment_id unique", "conservee"),
    "R-EQ-002": ("equipment", "criticality dans le domaine fermé", "conservee"),
    "R-EQ-003": ("equipment", "equipment_type normalisé", "conservee"),
    "R-EQ-004": ("equipment", "rated_power_kw strictement positive", "conservee"),
    "R-EQ-005": ("equipment", "commissioning_date antérieure à la fin de période", "conservee"),
    "R-EQ-006": ("equipment", "champs descriptifs renseignés", "conservee"),
    "R-EVT-001": ("events", "event_id unique", "conservee"),
    "R-EVT-002": ("events", "severity dans le domaine fermé", "conservee"),
    "R-EVT-003": ("events", "event_type normalisé et dans le domaine", "conservee"),
    "R-EVT-004": ("events", "end_at postérieure à start_at", "conservee"),
    "R-EVT-005": ("events", "equipment_id présent dans la table préparée", "conservee"),
    "R-MNT-001": ("maintenance", "maintenance_id unique", "conservee"),
    "R-MNT-002": ("maintenance", "event_id présent dans la table préparée", "conservee"),
    "R-MNT-003": ("maintenance", "equipment_id présent dans la table préparée", "conservee"),
    "R-MNT-004": ("maintenance", "closed_at postérieure à opened_at", "conservee"),
    "R-MNT-005": ("maintenance", "downtime_minutes positive et plausible", "conservee"),
    "R-MNT-006": ("maintenance", "parts_cost_eur positive", "conservee"),
    "R-MNT-007": (
        "maintenance",
        "intervention_type normalisé et dans le domaine",
        "modifiee",
    ),
    "R-MNT-008": (
        "maintenance",
        "absence d'information personnelle directe dans les notes",
        "etendue",
    ),
}

M2_RULE_JUSTIFICATIONS = {
    "R-MNT-007": (
        "Le registre de référence exclut MNT-2026S1-0912 après normalisation "
        "('Correctif' -> 'corrective', valeur pourtant valide), alors que "
        "R-EVT-003 traite une variante analogue par simple normalisation "
        "(ligne conservée). M3 aligne R-MNT-007 sur R-EVT-003 : normalisation "
        "puis conservation, sans exclusion, tant que la valeur normalisée "
        "appartient au domaine fermé. Voir docs/registre_regles.md."
    ),
    "R-MNT-008": (
        "Étendue à la détection d'un nom de personne (motif capitalisé), en "
        "plus de l'e-mail et du téléphone déjà couverts en M2, avec un "
        "marqueur typé par nature d'information ([email], [telephone], "
        "[personne]) plutôt qu'un jeton unique."
    ),
}

SENSOR_RULES: list[tuple[str, str, str]] = [
    ("SEN-KEY-001", "sensors", "unicité de la clé logique equipment_id + timestamp + sensor_name"),
    ("SEN-NAME-001", "sensors", "sensor_name normalisé"),
    ("SEN-UNIT-001", "sensors", "unité cohérente avec sensor_name, conversion vers l'unité canonique"),
    ("SEN-TZ-001", "sensors", "horodatage sans fuseau, UTC supposé"),
    ("SEN-RANGE-001", "sensors", "valeur dans la plage physique plausible du capteur, hors sentinelle"),
    ("SEN-PERIOD-001", "sensors", "period dans le périmètre annoncé de la livraison"),
    ("SEN-REF-001", "sensors", "equipment_id présent dans la table équipements préparée"),
    ("SEN-NULL-001", "sensors", "valeur manquante signalée, ligne conservée"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Contrôler les sources DiagOps M3")
    parser.add_argument("--input", type=Path, required=True, help="dossier des sources reçues")
    parser.add_argument("--output", type=Path, required=True, help="dossier des sorties")
    return parser


def build_registry() -> RuleRegistry:
    registry = RuleRegistry()
    for rule_id, (table, description, status) in M2_RULE_DESCRIPTIONS.items():
        registry.add(
            Rule(
                rule_id=rule_id,
                table=table,
                status=status,
                description=description,
                origin="M2",
                justification=M2_RULE_JUSTIFICATIONS.get(rule_id, ""),
            )
        )
    for rule_id, table, description in SENSOR_RULES:
        registry.add(
            Rule(rule_id=rule_id, table=table, status="nouvelle", description=description, origin="M3")
        )
    return registry


def _prepare_sensors(raw: pd.DataFrame, prepared_equipment: pd.DataFrame):
    checks: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []

    frame, records = sensor_rules.normalize_sensor_name(raw)
    quarantine += records
    frame, records = sensor_rules.normalize_units(frame)
    quarantine += records
    frame, records = sensor_rules.normalize_timestamps(frame)
    quarantine += records
    frame, records = sensor_rules.exclude_sentinel_values(frame)
    quarantine += records
    frame, records = sensor_rules.exclude_out_of_range_values(frame, sensor_value_ranges())
    quarantine += records
    frame, records = sensor_rules.exclude_out_of_announced_period(frame)
    quarantine += records
    frame, records = sensor_rules.exclude_unknown_equipment(frame, prepared_equipment["equipment_id"])
    quarantine += records
    frame, records = sensor_rules.resolve_duplicate_keys(frame)
    quarantine += records
    quarantine += sensor_rules.signal_missing_values(frame)

    by_rule: dict[str, int] = {}
    for record in quarantine:
        by_rule[record["rule_id"]] = by_rule.get(record["rule_id"], 0) + 1
    for rule_id, affected in by_rule.items():
        checks.append({"rule_id": rule_id, "source": "sensor_readings.csv", "affected_rows": affected})

    valid = True
    try:
        sensor_schema().validate(frame, lazy=True)
    except Exception:  # pandera.errors.SchemaErrors
        valid = False
    checks.append(
        {"rule_id": "SEN-SCHEMA-VALID", "source": "sensor_readings.csv", "affected_rows": 0 if valid else len(frame)}
    )

    return frame, quarantine, checks


def _prepare_m2_tables(sources: dict[str, pd.DataFrame]):
    checks: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []

    equipment, records = m2_rules.prepare_equipment(sources["equipment"])
    quarantine += records
    events, records_ev = m2_rules.prepare_events(sources["events"], equipment)
    quarantine += records_ev
    maintenance, records_mt = m2_rules.prepare_maintenance(sources["maintenance"], equipment, events)
    quarantine += records_mt

    by_rule: dict[str, tuple[str, int]] = {}
    for record in quarantine:
        key = record["rule_id"]
        source = record["source_file"]
        by_rule[key] = (source, by_rule.get(key, (source, 0))[1] + 1)
    for rule_id, (source, affected) in by_rule.items():
        checks.append({"rule_id": rule_id, "source": source, "affected_rows": affected})

    return {"equipment": equipment, "events": events, "maintenance": maintenance}, quarantine, checks


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sources = load_sources(args.input)
    checksums = source_checksums(args.input)

    for name in ("processed", "aggregates", "alignment"):
        (args.output / name).mkdir(parents=True, exist_ok=True)

    tables, m2_quarantine, m2_checks = _prepare_m2_tables(sources)
    sensors, sensor_quarantine, sensor_checks = _prepare_sensors(sources["sensors"], tables["equipment"])
    tables["sensors"] = sensors

    for name, frame in tables.items():
        frame.to_csv(args.output / "processed" / f"{name}.csv", index=False)

    aligned = align_measures_to_events(
        tables["sensors"], tables["events"], WINDOW_BEFORE_HOURS, WINDOW_AFTER_HOURS
    )
    aligned.to_csv(args.output / "alignment" / "measures_events.csv", index=False)

    aggregates = (
        aligned.groupby(["event_id", "equipment_id", "sensor_name"])
        .agg(
            measurements=("value", "size"),
            completeness=("value", lambda s: float(s.notna().mean())),
            minimum=("value", "min"),
            maximum=("value", "max"),
            mean=("value", "mean"),
            std=("value", "std"),
        )
        .reset_index()
    )
    aggregates.to_csv(args.output / "aggregates" / "measures_by_event_window.csv", index=False)

    frozen = sensor_rules.flag_frozen_runs(sources["sensors"])
    frozen.to_csv(args.output / "aggregates" / "frozen_runs.csv", index=False)

    overview_raw = series_overview(sources["sensors"])
    overview_raw.to_csv(args.output / "series_overview_raw.csv", index=False)
    overview_prepared = series_overview(tables["sensors"])
    overview_prepared.to_csv(args.output / "series_overview.csv", index=False)

    quarantine_records = m2_quarantine + sensor_quarantine
    quarantine_df = (
        quarantine_frame(quarantine_records) if quarantine_records else pd.DataFrame(columns=QUARANTINE_COLUMNS)
    )
    quarantine_df = merge_quarantines(quarantine_df)
    quarantine_df.to_csv(args.output / "quarantine.csv", index=False)

    registry = build_registry()
    registry.to_frame().to_csv(args.output / "registre_regles.csv", index=False)
    (args.output / "registre_regles.md").write_text(registry.to_markdown(), encoding="utf-8")

    n_events_total = len(tables["events"])
    n_events_matched = int(aligned["event_id"].nunique())
    n_instrumented_equipment = int(tables["sensors"]["equipment_id"].nunique())

    all_checks = m2_checks + sensor_checks
    rule_table = {rule.rule_id: rule.table for rule in registry.rules}
    checked_rule_ids = {check["rule_id"] for check in all_checks}
    for rule in registry.rules:
        if rule.rule_id in checked_rule_ids or rule.rule_id == "SEN-SCHEMA-VALID":
            continue
        all_checks.append({"rule_id": rule.rule_id, "source": rule_table[rule.rule_id], "affected_rows": 0})
    quarantined_rows = int(
        quarantine_df["decision"].isin(["doublon_supprime", "exclue"]).sum()
    )

    report = {
        "status": "completed",
        "sources": {
            name: {"rows": len(frame), "sha256": checksums[name]} for name, frame in sources.items()
        },
        "processed_rows": {name: len(frame) for name, frame in tables.items()},
        "checks": all_checks,
        "rules": {
            "declared": len(registry.rules),
            "active": len(registry.active()),
        },
        "alignment": {
            "window_before_hours": WINDOW_BEFORE_HOURS,
            "window_after_hours": WINDOW_AFTER_HOURS,
            "events_total": n_events_total,
            "events_matched": n_events_matched,
            "events_unmatched": n_events_total - n_events_matched,
            "instrumented_equipment": n_instrumented_equipment,
            "aligned_rows": len(aligned),
        },
        "summary": {
            "passed": sum(1 for c in all_checks if c["affected_rows"] == 0),
            "failed": sum(1 for c in all_checks if c["affected_rows"] > 0),
            "quarantined_rows": quarantined_rows,
        },
        "decision": "utilisable sous conditions",
    }
    (args.output / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0
