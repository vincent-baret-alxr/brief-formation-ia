import pandas as pd
import pandera.pandas as pa
import pytest

from contracts.schemas import sensor_schema, sensor_value_ranges
from src.data_pipeline import sensor_rules as sr


def _row(**overrides):
    row = {
        "equipment_id": "EQ-PUMP-001",
        "timestamp": "2026-01-02T00:00:00Z",
        "sensor_name": "vibration_mm_s",
        "value": 2.8,
        "unit": "mm/s",
        "period": "2026-S1",
    }
    row.update(overrides)
    return row


def test_normalize_sensor_name_fixes_case_and_space():
    frame = pd.DataFrame([_row(sensor_name="TEMPERATURE_C ", unit="°C")])
    fixed, records = sr.normalize_sensor_name(frame)
    assert fixed.loc[0, "sensor_name"] == "temperature_c"
    assert len(records) == 1


def test_normalize_sensor_name_leaves_valid_name_untouched():
    frame = pd.DataFrame([_row()])
    fixed, records = sr.normalize_sensor_name(frame)
    assert fixed.loc[0, "sensor_name"] == "vibration_mm_s"
    assert records == []


def test_normalize_units_converts_kelvin_to_celsius():
    frame = pd.DataFrame([_row(sensor_name="temperature_c", value=330.0, unit="K")])
    fixed, records = sr.normalize_units(frame)
    assert fixed.loc[0, "unit"] == "°C"
    assert fixed.loc[0, "value"] == pytest.approx(330.0 - 273.15)
    assert len(records) == 1


def test_normalize_units_converts_kilopascal_to_bar():
    frame = pd.DataFrame([_row(sensor_name="pressure_bar", value=577.0, unit="kPa")])
    fixed, records = sr.normalize_units(frame)
    assert fixed.loc[0, "unit"] == "bar"
    assert fixed.loc[0, "value"] == pytest.approx(5.77)


def test_exclude_sentinel_values_removes_minus_999():
    frame = pd.DataFrame([_row(value=-999.0), _row(value=2.9)])
    fixed, records = sr.exclude_sentinel_values(frame)
    assert len(fixed) == 1
    assert fixed.iloc[0]["value"] == 2.9
    assert len(records) == 1
    assert records[0]["decision"] == "exclue"


def test_exclude_out_of_range_values_keeps_plausible_reading():
    frame = pd.DataFrame([_row(value=2.9)])
    fixed, records = sr.exclude_out_of_range_values(frame, sensor_value_ranges())
    assert len(fixed) == 1
    assert records == []


def test_exclude_out_of_range_values_rejects_impossible_reading():
    frame = pd.DataFrame([_row(sensor_name="rpm", unit="rpm", value=50_000.0)])
    fixed, records = sr.exclude_out_of_range_values(frame, sensor_value_ranges())
    assert len(fixed) == 0
    assert len(records) == 1


def test_exclude_out_of_announced_period_removes_other_periods():
    frame = pd.DataFrame([_row(period="2026-S1"), _row(period="2026-S2")])
    fixed, records = sr.exclude_out_of_announced_period(frame)
    assert len(fixed) == 1
    assert len(records) == 1
    assert records[0]["decision"] == "exclue"


def test_exclude_unknown_equipment_removes_unreferenced_equipment():
    frame = pd.DataFrame([_row(equipment_id="EQ-ORPHAN-777"), _row()])
    fixed, records = sr.exclude_unknown_equipment(frame, pd.Series(["EQ-PUMP-001"]))
    assert len(fixed) == 1
    assert fixed.iloc[0]["equipment_id"] == "EQ-PUMP-001"
    assert len(records) == 1


def test_resolve_duplicate_keys_drops_only_extra_strict_copy():
    frame = pd.DataFrame([_row(), _row()])
    fixed, records = sr.resolve_duplicate_keys(frame)
    assert len(fixed) == 1
    assert len(records) == 1
    assert records[0]["decision"] == "doublon_supprime"


def test_resolve_duplicate_keys_excludes_both_divergent_copies():
    frame = pd.DataFrame([_row(value=1.0), _row(value=9.0)])
    fixed, records = sr.resolve_duplicate_keys(frame)
    assert len(fixed) == 0
    assert len(records) == 2
    assert all(r["decision"] == "exclue" for r in records)


def test_signal_missing_values_keeps_row_and_flags_it():
    frame = pd.DataFrame([_row(value=None)])
    records = sr.signal_missing_values(frame)
    assert len(records) == 1
    assert records[0]["decision"] == "conserve_signale"


def test_flag_frozen_runs_detects_a_long_repeated_sequence():
    rows = [_row(timestamp=f"2026-01-{day:02d}T00:00:00Z", value=2.8) for day in range(1, 9)]
    frame = pd.DataFrame(rows)
    frozen = sr.flag_frozen_runs(frame, min_run=6)
    assert len(frozen) == 1
    assert frozen.iloc[0]["run_length"] == 8


def test_flag_frozen_runs_ignores_a_normally_varying_series():
    rows = [_row(timestamp=f"2026-01-{day:02d}T00:00:00Z", value=2.0 + 0.1 * day) for day in range(1, 9)]
    frame = pd.DataFrame(rows)
    frozen = sr.flag_frozen_runs(frame, min_run=6)
    assert frozen.empty


def test_sensor_schema_accepts_a_clean_reading():
    frame = pd.DataFrame([_row()])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    sensor_schema().validate(frame, lazy=True)


def test_sensor_schema_rejects_a_value_outside_the_physical_range():
    frame = pd.DataFrame([_row(sensor_name="current_a", unit="A", value=-999.0)])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    with pytest.raises(pa.errors.SchemaErrors):
        sensor_schema().validate(frame, lazy=True)


def test_sensor_schema_accepts_a_missing_value():
    frame = pd.DataFrame([_row(value=None)])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["value"] = frame["value"].astype(float)
    sensor_schema().validate(frame, lazy=True)
