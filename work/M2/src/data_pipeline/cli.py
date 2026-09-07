"""Pipeline de préparation des données DiagOps M2.

Étapes, dans l'ordre, toutes rejouables depuis les fichiers reçus :

1. charger les trois sources brutes (jamais modifiées sur disque) ;
2. corriger les variantes de catégorie non ambiguës et masquer les
   informations personnelles détectées (journal avant/après) ;
3. écarter les doublons stricts et les ruptures d'intégrité référentielle ;
4. valider le reste par les contrats Pandera de ``contracts.schemas`` et
   écarter les lignes non conformes ;
5. écrire les tables préparées, la quarantaine et le rapport de validation.

Le statut ``starter_to_complete`` du point de départ est remplacé par un
rapport réel.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pandera.pandas as pa

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from contracts.schemas import (  # noqa: E402
    equipment_schema,
    events_schema,
    maintenance_schema,
)

from .io import load_sources, source_checksums
from .quarantine import QUARANTINE_COLUMNS, quarantine_frame
from .rules import (
    CORRECTION_COLUMNS,
    DATE_COLUMNS,
    ID_COLUMNS,
    apply_category_fixes,
    duplicate_row_mask,
    mask_pii_in_notes,
    parse_dates,
    quarantine_records_from_mask,
    referential_breaks,
    schema_failures_to_quarantine,
)

SCHEMAS = {
    "equipment": equipment_schema,
    "events": events_schema,
    "maintenance": maintenance_schema,
}

# events.start_at / end_at et maintenance.opened_at / closed_at sont horodatés
# ISO 8601 avec fuseau (schémas en UTC) ; equipment.commissioning_date est une
# date locale sans fuseau.
UTC_TABLES = {"events", "maintenance"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Contrôler les données DiagOps M2")
    parser.add_argument("--input", type=Path, required=True, help="dossier des CSV reçus")
    parser.add_argument("--output", type=Path, required=True, help="dossier des sorties")
    return parser


def _run_schema(name: str, frame: pd.DataFrame) -> tuple[bool, pd.DataFrame | None]:
    """Valide ``frame`` avec le schéma Pandera nommé ``name``.

    Retourne ``(valide, failure_cases)`` : ``failure_cases`` est ``None`` si
    la validation réussit.
    """
    schema = SCHEMAS[name]()
    try:
        schema.validate(frame, lazy=True)
        return True, None
    except pa.errors.SchemaErrors as exc:
        return False, exc.failure_cases


def _prepare_table(
    name: str, raw: pd.DataFrame
) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Nettoie une table et retourne (table_préparée, corrections, quarantaine, checks)."""
    id_column = ID_COLUMNS[name]
    corrections: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []

    frame = parse_dates(raw, DATE_COLUMNS[name], utc=name in UTC_TABLES)

    frame, fix_records = apply_category_fixes(frame, f"{name}.csv", id_column)
    corrections.extend(fix_records)
    for rule_id in {r["rule_id"] for r in fix_records}:
        affected = sum(1 for r in fix_records if r["rule_id"] == rule_id)
        checks.append(
            {"rule_id": rule_id, "source": f"{name}.csv", "passed": False, "affected_rows": affected}
        )

    if name == "maintenance":
        frame, pii_records = mask_pii_in_notes(frame, f"{name}.csv", id_column)
        corrections.extend(pii_records)
        if pii_records:
            checks.append(
                {
                    "rule_id": "PII_DETECTED_IN_NOTE",
                    "source": f"{name}.csv",
                    "passed": False,
                    "affected_rows": len(pii_records),
                }
            )

    quarantine: list[dict[str, Any]] = []

    dup_mask = duplicate_row_mask(frame)
    dup_records = quarantine_records_from_mask(
        frame,
        dup_mask,
        f"{name}.csv",
        id_column,
        rule_id="DUPLICATE_ROW",
        column=id_column,
        reason="Ligne strictement identique à une ligne déjà retenue.",
        decision="exclu_doublon",
    )
    quarantine.extend(dup_records)
    checks.append(
        {
            "rule_id": "DUPLICATE_ROW",
            "source": f"{name}.csv",
            "passed": len(dup_records) == 0,
            "affected_rows": len(dup_records),
        }
    )
    frame = frame.loc[~dup_mask]

    return frame, corrections, quarantine, checks


def _check_referential_integrity(
    tables: dict[str, pd.DataFrame],
    quarantine_by_table: dict[str, list[dict[str, Any]]],
    checks: list[dict[str, Any]],
) -> None:
    equipment_ids = tables["equipment"][ID_COLUMNS["equipment"]]

    for name, column, reason in [
        ("events", "equipment_id", "equipment_id absent de equipment.csv."),
        ("maintenance", "equipment_id", "equipment_id absent de equipment.csv."),
    ]:
        mask = referential_breaks(tables[name], column, equipment_ids)
        records = quarantine_records_from_mask(
            tables[name],
            mask,
            f"{name}.csv",
            ID_COLUMNS[name],
            rule_id="UNKNOWN_EQUIPMENT_ID",
            column=column,
            reason=reason,
            decision="exclu_reference_rompue",
        )
        quarantine_by_table[name].extend(records)
        checks.append(
            {
                "rule_id": "UNKNOWN_EQUIPMENT_ID",
                "source": f"{name}.csv",
                "passed": len(records) == 0,
                "affected_rows": len(records),
            }
        )
        tables[name] = tables[name].loc[~mask]

    event_ids = tables["events"][ID_COLUMNS["events"]]
    mask = referential_breaks(tables["maintenance"], "event_id", event_ids)
    records = quarantine_records_from_mask(
        tables["maintenance"],
        mask,
        "maintenance.csv",
        ID_COLUMNS["maintenance"],
        rule_id="UNKNOWN_EVENT_ID",
        column="event_id",
        reason="event_id absent de events.csv.",
        decision="exclu_reference_rompue",
    )
    quarantine_by_table["maintenance"].extend(records)
    checks.append(
        {
            "rule_id": "UNKNOWN_EVENT_ID",
            "source": "maintenance.csv",
            "passed": len(records) == 0,
            "affected_rows": len(records),
        }
    )
    tables["maintenance"] = tables["maintenance"].loc[~mask]


def _apply_schema_quarantine(
    tables: dict[str, pd.DataFrame],
    quarantine_by_table: dict[str, list[dict[str, Any]]],
    checks: list[dict[str, Any]],
) -> None:
    for name, frame in tables.items():
        valid, failure_cases = _run_schema(name, frame)
        if valid:
            checks.append(
                {
                    "rule_id": "SCHEMA_VALID_PRE_QUARANTINE",
                    "source": f"{name}.csv",
                    "passed": True,
                    "affected_rows": 0,
                }
            )
            continue

        records = schema_failures_to_quarantine(
            failure_cases, frame, f"{name}.csv", ID_COLUMNS[name]
        )
        quarantine_by_table[name].extend(records)
        by_rule: dict[str, int] = {}
        for record in records:
            by_rule[record["rule_id"]] = by_rule.get(record["rule_id"], 0) + 1
        for rule_id, affected in by_rule.items():
            checks.append(
                {"rule_id": rule_id, "source": f"{name}.csv", "passed": False, "affected_rows": affected}
            )

        bad_identifiers = {record["row_identifier"] for record in records}
        tables[name] = frame.loc[~frame[ID_COLUMNS[name]].isin(bad_identifiers)]


def decide(quarantined_rows: int, total_rows: int, checks: list[dict[str, Any]]) -> str:
    """Applique la règle de décision du brief M2 : utilisable / sous conditions / non utilisable."""
    has_unresolved_reference_break = any(
        c["rule_id"] in {"UNKNOWN_EQUIPMENT_ID", "UNKNOWN_EVENT_ID"} and c["affected_rows"] > 0
        for c in checks
    )
    quarantine_rate = quarantined_rows / total_rows if total_rows else 0.0
    if quarantine_rate == 0:
        return "utilisable"
    if quarantine_rate > 0.05:
        return "non utilisable en l'état"
    if has_unresolved_reference_break:
        return "utilisable sous conditions"
    return "utilisable sous conditions"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw_sources = load_sources(args.input)
    checksums = source_checksums(args.input)

    args.output.mkdir(parents=True, exist_ok=True)
    processed_dir = args.output / "processed"
    processed_dir.mkdir(exist_ok=True)

    all_corrections: list[dict[str, Any]] = []
    quarantine_by_table: dict[str, list[dict[str, Any]]] = {name: [] for name in raw_sources}
    checks: list[dict[str, Any]] = []
    tables: dict[str, pd.DataFrame] = {}

    for name, raw in raw_sources.items():
        frame, corrections, dup_quarantine, table_checks = _prepare_table(name, raw)
        tables[name] = frame
        all_corrections.extend(corrections)
        quarantine_by_table[name].extend(dup_quarantine)
        checks.extend(table_checks)

    _check_referential_integrity(tables, quarantine_by_table, checks)
    _apply_schema_quarantine(tables, quarantine_by_table, checks)

    # Confirmation finale : les tables retenues respectent bien le contrat.
    for name, frame in tables.items():
        valid, _ = _run_schema(name, frame)
        checks.append(
            {
                "rule_id": "PROCESSED_TABLE_SCHEMA_VALID",
                "source": f"{name}.csv",
                "passed": valid,
                "affected_rows": 0 if valid else len(frame),
            }
        )

    for name, frame in tables.items():
        out = frame.copy()
        for column in DATE_COLUMNS[name]:
            out[column] = out[column].apply(
                lambda value: value.isoformat() if pd.notna(value) else ""
            )
        out.to_csv(processed_dir / f"{name}.csv", index=False)

    all_quarantine_records = [
        record for records in quarantine_by_table.values() for record in records
    ]
    quarantine_df = (
        quarantine_frame(all_quarantine_records)
        if all_quarantine_records
        else pd.DataFrame(columns=QUARANTINE_COLUMNS)
    )
    quarantine_df.to_csv(args.output / "quarantine.csv", index=False)

    corrections_df = (
        pd.DataFrame(all_corrections)
        if all_corrections
        else pd.DataFrame(columns=CORRECTION_COLUMNS)
    )
    if all_corrections:
        corrections_df = corrections_df.loc[:, CORRECTION_COLUMNS]
    corrections_df.to_csv(args.output / "corrections.csv", index=False)

    total_raw_rows = sum(len(frame) for frame in raw_sources.values())
    quarantined_rows = len(all_quarantine_records)
    passed = sum(1 for c in checks if c["passed"])
    failed = sum(1 for c in checks if not c["passed"])

    report = {
        "status": "completed",
        "message": "Pipeline M2 exécuté : corrections, quarantaine et validation Pandera appliquées.",
        "sources": {
            name: {"rows": len(frame), "sha256": checksums[name]}
            for name, frame in raw_sources.items()
        },
        "checks": checks,
        "summary": {
            "passed": passed,
            "failed": failed,
            "quarantined_rows": quarantined_rows,
            "corrected_values": len(all_corrections),
            "total_raw_rows": total_raw_rows,
        },
        "decision": decide(quarantined_rows, total_raw_rows, checks),
    }
    (args.output / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0
