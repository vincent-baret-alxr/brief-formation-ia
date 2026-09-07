import pandas as pd

from src.data_pipeline.m2_rules import (
    prepare_equipment,
    prepare_events,
    prepare_maintenance,
)


def _equipment_row(**overrides):
    row = {
        "equipment_id": "EQ-PUMP-001",
        "equipment_type": "pump",
        "site_id": "SITE-SUD",
        "commissioning_date": "2020-01-01",
        "criticality": "medium",
        "manufacturer": "Valcor",
        "rated_power_kw": 42.0,
    }
    row.update(overrides)
    return row


def test_prepare_equipment_removes_strict_duplicate():
    frame = pd.DataFrame([_equipment_row(), _equipment_row()])
    prepared, quarantine = prepare_equipment(frame)
    assert len(prepared) == 1
    assert any(r["rule_id"] == "R-EQ-001" and r["decision"] == "doublon_supprime" for r in quarantine)


def test_prepare_equipment_normalizes_category_typo_and_keeps_row():
    frame = pd.DataFrame([_equipment_row(equipment_type="Pump ")])
    prepared, quarantine = prepare_equipment(frame)
    assert len(prepared) == 1
    assert prepared.iloc[0]["equipment_type"] == "pump"
    assert any(r["rule_id"] == "R-EQ-003" for r in quarantine)


def test_prepare_equipment_neutralizes_negative_power_but_keeps_row():
    frame = pd.DataFrame([_equipment_row(rated_power_kw=-12.5)])
    prepared, quarantine = prepare_equipment(frame)
    assert len(prepared) == 1
    assert pd.isna(prepared.iloc[0]["rated_power_kw"])
    assert any(r["rule_id"] == "R-EQ-004" and r["decision"] == "champ_neutralise" for r in quarantine)


def test_prepare_equipment_signals_missing_manufacturer_without_touching_the_row():
    frame = pd.DataFrame([_equipment_row(manufacturer=None)])
    prepared, quarantine = prepare_equipment(frame)
    assert len(prepared) == 1
    assert pd.isna(prepared.iloc[0]["manufacturer"])
    assert any(r["rule_id"] == "R-EQ-006" and r["decision"] == "conserve_signale" for r in quarantine)


def test_prepare_equipment_accepts_a_clean_row_without_any_quarantine():
    frame = pd.DataFrame([_equipment_row()])
    prepared, quarantine = prepare_equipment(frame)
    assert len(prepared) == 1
    assert quarantine == []


def _event_row(**overrides):
    row = {
        "event_id": "EVT-0001",
        "equipment_id": "EQ-PUMP-001",
        "start_at": "2026-01-01T00:00:00Z",
        "end_at": "2026-01-01T02:00:00Z",
        "event_type": "incident",
        "severity": "high",
        "period": "2026-S1",
    }
    row.update(overrides)
    return row


def _prepared_equipment():
    return pd.DataFrame([_equipment_row()])


def test_prepare_events_excludes_severity_outside_domain():
    frame = pd.DataFrame([_event_row(severity="URGENT")])
    prepared, quarantine = prepare_events(frame, _prepared_equipment())
    assert len(prepared) == 0
    assert any(r["rule_id"] == "R-EVT-002" and r["decision"] == "exclue" for r in quarantine)


def test_prepare_events_excludes_unknown_equipment_reference():
    frame = pd.DataFrame([_event_row(equipment_id="EQ-ORPHAN-999")])
    prepared, quarantine = prepare_events(frame, _prepared_equipment())
    assert len(prepared) == 0
    assert any(r["rule_id"] == "R-EVT-005" for r in quarantine)


def test_prepare_events_keeps_a_reference_to_a_neutralized_equipment_field():
    equipment = pd.DataFrame([_equipment_row(rated_power_kw=-1.0)])
    prepared_equipment, _ = prepare_equipment(equipment)
    frame = pd.DataFrame([_event_row()])
    prepared, quarantine = prepare_events(frame, prepared_equipment)
    assert len(prepared) == 1  # equipment reste référençable malgré le champ neutralisé


def _maintenance_row(**overrides):
    row = {
        "maintenance_id": "MNT-0001",
        "event_id": "EVT-0001",
        "equipment_id": "EQ-PUMP-001",
        "opened_at": "2026-01-01T00:00:00Z",
        "closed_at": "2026-01-01T05:00:00Z",
        "intervention_type": "corrective",
        "outcome": "resolved",
        "downtime_minutes": 120,
        "labor_hours": 2.5,
        "parts_cost_eur": 100.0,
        "parts_replaced_count": 1,
        "work_order_note": "Intervention conforme.",
        "period": "2026-S1",
    }
    row.update(overrides)
    return row


def _prepared_events():
    return pd.DataFrame([_event_row()])


def test_prepare_maintenance_excludes_sentinel_downtime_is_kept_but_negative_is_excluded():
    frame = pd.DataFrame(
        [_maintenance_row(maintenance_id="MNT-A", downtime_minutes=99999),
         _maintenance_row(maintenance_id="MNT-B", downtime_minutes=-45)]
    )
    prepared, quarantine = prepare_maintenance(frame, _prepared_equipment(), _prepared_events())
    assert set(prepared["maintenance_id"]) == {"MNT-A"}
    sentinel = next(r for r in quarantine if r["row_identifier"] == "MNT-A")
    assert sentinel["decision"] == "conserve_signale"
    negative = next(r for r in quarantine if r["row_identifier"] == "MNT-B")
    assert negative["decision"] == "exclue"


def test_prepare_maintenance_translates_french_intervention_type_and_keeps_row():
    frame = pd.DataFrame([_maintenance_row(intervention_type="Correctif")])
    prepared, quarantine = prepare_maintenance(frame, _prepared_equipment(), _prepared_events())
    assert len(prepared) == 1
    assert prepared.iloc[0]["intervention_type"] == "corrective"
    assert any(r["rule_id"] == "R-MNT-007" and r["decision"] == "valeur_normalisee" for r in quarantine)


def test_prepare_maintenance_pseudonymizes_email_phone_and_name():
    frame = pd.DataFrame(
        [_maintenance_row(work_order_note="Rappeler Nadia B. au 06 12 34 56 78, cc a.b@example.test")]
    )
    prepared, quarantine = prepare_maintenance(frame, _prepared_equipment(), _prepared_events())
    note = prepared.iloc[0]["work_order_note"]
    assert "Nadia" not in note
    assert "06 12 34 56 78" not in note
    assert "example.test" not in note
    assert "[personne]" in note and "[telephone]" in note and "[email]" in note
    assert any(r["rule_id"] == "R-MNT-008" for r in quarantine)


def test_prepare_maintenance_excludes_reference_to_an_excluded_event_cascade():
    # L'événement est hors domaine (sévérité invalide) : il est exclu de la
    # table préparée, ce qui doit à son tour exclure l'intervention qui le
    # référence (cascade documentée dans docs/registre_regles.md).
    events = pd.DataFrame([_event_row(severity="URGENT")])
    prepared_events, _ = prepare_events(events, _prepared_equipment())
    frame = pd.DataFrame([_maintenance_row()])
    prepared, quarantine = prepare_maintenance(frame, _prepared_equipment(), prepared_events)
    assert len(prepared) == 0
    assert any(r["rule_id"] == "R-MNT-002" for r in quarantine)
