"""Démontre l'absence de régression par rapport à la préparation de référence M2.

`data_pack/2026-S1/reference_runs/m2_for_m3/` documente, pour chaque règle
`R-EQ-*` / `R-EVT-*` / `R-MNT-*`, le nombre de lignes affectées
(`analyses/rapport_validation_m2.json`). Ces tests rejouent les mêmes règles
sur les fichiers reçus et comparent les effectifs, rule par rule, à cette
référence.

Seule `R-MNT-007` diverge, de façon délibérée et justifiée (voir
`docs/registre_regles.md` et `src/data_pipeline/m2_rules.py`) : ce test la
vérifie explicitement plutôt que de l'ignorer silencieusement.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd
import pytest

from src.data_pipeline.io import data_dir
from src.data_pipeline.m2_rules import prepare_equipment, prepare_events, prepare_maintenance

REFERENCE_DIR = data_dir() / "reference_runs" / "m2_for_m3"


def _reference_available() -> bool:
    return (REFERENCE_DIR / "analyses" / "rapport_validation_m2.json").is_file()


pytestmark = pytest.mark.skipif(
    not _reference_available(), reason="Référence M2 absente de data_pack/"
)


@pytest.fixture(scope="module")
def prepared():
    base = data_dir()
    equipment = pd.read_csv(base / "equipment" / "equipment.csv")
    events = pd.read_csv(base / "events" / "events.csv")
    maintenance = pd.read_csv(base / "maintenance" / "maintenance_history.csv")

    prepared_equipment, q_eq = prepare_equipment(equipment)
    prepared_events, q_ev = prepare_events(events, prepared_equipment)
    prepared_maintenance, q_mt = prepare_maintenance(maintenance, prepared_equipment, prepared_events)

    return {
        "equipment": prepared_equipment,
        "events": prepared_events,
        "maintenance": prepared_maintenance,
        "quarantine": q_eq + q_ev + q_mt,
    }


@pytest.fixture(scope="module")
def reference_report():
    with (REFERENCE_DIR / "analyses" / "rapport_validation_m2.json").open(encoding="utf-8") as handle:
        return json.load(handle)


DELIBERATE_DIVERGENCES = {"R-MNT-007"}


def test_row_counts_match_reference_except_the_declared_divergence(prepared, reference_report):
    expected = reference_report["sources"]
    assert len(prepared["equipment"]) == expected["equipment.csv"]["rows_out"]
    assert len(prepared["events"]) == expected["events.csv"]["rows_out"]
    # R-MNT-007 modifiée conserve une ligne que la référence exclut : +1 ligne.
    assert len(prepared["maintenance"]) == expected["maintenance_history.csv"]["rows_out"] + 1


def test_every_conserved_rule_reproduces_the_reference_affected_rows(prepared, reference_report):
    observed = Counter(record["rule_id"] for record in prepared["quarantine"])
    expected_by_rule = {check["rule_id"]: check["affected_rows"] for check in reference_report["checks"]}

    mismatches = []
    for rule_id, expected_count in expected_by_rule.items():
        if rule_id in DELIBERATE_DIVERGENCES:
            continue
        if observed.get(rule_id, 0) != expected_count:
            mismatches.append((rule_id, expected_count, observed.get(rule_id, 0)))

    assert mismatches == []


def test_the_declared_divergence_is_the_only_one(prepared, reference_report):
    observed = Counter(record["rule_id"] for record in prepared["quarantine"])
    expected_by_rule = {check["rule_id"]: check["affected_rows"] for check in reference_report["checks"]}
    # R-MNT-007 : la référence journalise 2 entrées (normalisation + exclusion
    # jugée incohérente, voir docs/registre_regles.md) ; M3 n'en journalise
    # qu'une (normalisation seule, ligne conservée).
    assert expected_by_rule["R-MNT-007"] == 2
    assert observed["R-MNT-007"] == 1


def test_all_identifiers_stay_unique_after_preparation(prepared):
    assert prepared["equipment"]["equipment_id"].is_unique
    assert prepared["events"]["event_id"].is_unique
    assert prepared["maintenance"]["maintenance_id"].is_unique
