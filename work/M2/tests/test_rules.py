import pandas as pd
import pandera.pandas as pa
import pytest

from contracts.schemas import equipment_schema, events_schema, maintenance_schema
from src.data_pipeline.rules import (
    apply_category_fixes,
    duplicate_row_mask,
    mask_pii_in_notes,
    referential_breaks,
)


def _valid_equipment_row(**overrides):
    row = {
        "equipment_id": "EQ-PUMP-001",
        "equipment_type": "pump",
        "site_id": "SITE-SUD",
        "commissioning_date": pd.Timestamp("2020-01-01"),
        "criticality": "medium",
        "manufacturer": "Valcor",
        "rated_power_kw": 42.0,
    }
    row.update(overrides)
    return row


def test_equipment_schema_accepts_a_valid_row():
    frame = pd.DataFrame([_valid_equipment_row()])
    equipment_schema().validate(frame, lazy=True)  # ne doit pas lever


def test_equipment_schema_rejects_negative_power():
    frame = pd.DataFrame([_valid_equipment_row(rated_power_kw=-12.5)])
    with pytest.raises(pa.errors.SchemaErrors):
        equipment_schema().validate(frame, lazy=True)


def test_equipment_schema_rejects_future_commissioning_date():
    frame = pd.DataFrame(
        [_valid_equipment_row(commissioning_date=pd.Timestamp.now() + pd.Timedelta(days=365))]
    )
    with pytest.raises(pa.errors.SchemaErrors):
        equipment_schema().validate(frame, lazy=True)


def test_equipment_schema_accepts_null_manufacturer_and_power():
    frame = pd.DataFrame([_valid_equipment_row(manufacturer=None, rated_power_kw=None)])
    frame["rated_power_kw"] = frame["rated_power_kw"].astype(float)
    equipment_schema().validate(frame, lazy=True)  # nullable d'après SCHEMA.md


def test_equipment_schema_rejects_unknown_category():
    frame = pd.DataFrame([_valid_equipment_row(equipment_type="Pump ")])
    with pytest.raises(pa.errors.SchemaErrors):
        equipment_schema().validate(frame, lazy=True)


def _valid_event_row(**overrides):
    row = {
        "event_id": "EVT-0001",
        "equipment_id": "EQ-PUMP-001",
        "start_at": pd.Timestamp("2026-01-01T00:00:00Z"),
        "end_at": pd.Timestamp("2026-01-01T02:00:00Z"),
        "event_type": "incident",
        "severity": "high",
        "period": "2026-S1",
    }
    row.update(overrides)
    return row


def test_events_schema_accepts_open_event_without_end_at():
    frame = pd.DataFrame([_valid_event_row(end_at=None)])
    frame["end_at"] = pd.to_datetime(frame["end_at"], utc=True)
    events_schema().validate(frame, lazy=True)


def test_events_schema_rejects_end_before_start():
    frame = pd.DataFrame(
        [_valid_event_row(end_at=pd.Timestamp("2025-12-31T00:00:00Z"))]
    )
    with pytest.raises(pa.errors.SchemaErrors):
        events_schema().validate(frame, lazy=True)


def test_events_schema_rejects_severity_outside_enum():
    frame = pd.DataFrame([_valid_event_row(severity="URGENT")])
    with pytest.raises(pa.errors.SchemaErrors):
        events_schema().validate(frame, lazy=True)


def _valid_maintenance_row(**overrides):
    row = {
        "maintenance_id": "MNT-0001",
        "event_id": "EVT-0001",
        "equipment_id": "EQ-PUMP-001",
        "opened_at": pd.Timestamp("2026-01-01T00:00:00Z"),
        "closed_at": pd.Timestamp("2026-01-01T05:00:00Z"),
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


def test_maintenance_schema_rejects_sentinel_downtime():
    frame = pd.DataFrame([_valid_maintenance_row(downtime_minutes=99999)])
    with pytest.raises(pa.errors.SchemaErrors):
        maintenance_schema().validate(frame, lazy=True)


def test_maintenance_schema_rejects_negative_parts_cost():
    frame = pd.DataFrame([_valid_maintenance_row(parts_cost_eur=-350.0)])
    with pytest.raises(pa.errors.SchemaErrors):
        maintenance_schema().validate(frame, lazy=True)


def test_maintenance_schema_accepts_still_open_intervention():
    frame = pd.DataFrame([_valid_maintenance_row(closed_at=None)])
    frame["closed_at"] = pd.to_datetime(frame["closed_at"], utc=True)
    maintenance_schema().validate(frame, lazy=True)


def test_duplicate_row_mask_flags_only_repeated_rows():
    frame = pd.DataFrame(
        [
            {"equipment_id": "EQ-1", "value": 1},
            {"equipment_id": "EQ-2", "value": 2},
            {"equipment_id": "EQ-1", "value": 1},
        ]
    )
    mask = duplicate_row_mask(frame)
    assert mask.tolist() == [False, False, True]


def test_referential_breaks_detects_missing_parent_id():
    child = pd.DataFrame({"equipment_id": ["EQ-1", "EQ-999"]})
    parent_ids = pd.Series(["EQ-1", "EQ-2"])
    mask = referential_breaks(child, "equipment_id", parent_ids)
    assert mask.tolist() == [False, True]


def test_apply_category_fixes_normalizes_known_typo():
    frame = pd.DataFrame([{"equipment_id": "EQ-1", "equipment_type": "Pump "}])
    fixed, records = apply_category_fixes(frame, "equipment.csv", "equipment_id")
    assert fixed.loc[0, "equipment_type"] == "pump"
    assert records[0]["before"] == "Pump "
    assert records[0]["after"] == "pump"


def test_apply_category_fixes_leaves_valid_category_untouched():
    frame = pd.DataFrame([{"equipment_id": "EQ-1", "equipment_type": "pump"}])
    fixed, records = apply_category_fixes(frame, "equipment.csv", "equipment_id")
    assert fixed.loc[0, "equipment_type"] == "pump"
    assert records == []


def test_mask_pii_in_notes_masks_email_and_phone():
    frame = pd.DataFrame(
        [
            {"maintenance_id": "MNT-1", "work_order_note": "Contact : a.b@example.test"},
            {"maintenance_id": "MNT-2", "work_order_note": "Rappeler au 06 12 34 56 78."},
        ]
    )
    masked, records = mask_pii_in_notes(frame, "maintenance.csv", "maintenance_id")
    assert "example.test" not in masked.loc[0, "work_order_note"]
    assert "06 12 34 56 78" not in masked.loc[1, "work_order_note"]
    assert len(records) == 2


def test_mask_pii_in_notes_leaves_technical_note_untouched():
    frame = pd.DataFrame(
        [{"maintenance_id": "MNT-1", "work_order_note": "Pièce remplacée, RAS."}]
    )
    masked, records = mask_pii_in_notes(frame, "maintenance.csv", "maintenance_id")
    assert masked.loc[0, "work_order_note"] == "Pièce remplacée, RAS."
    assert records == []
