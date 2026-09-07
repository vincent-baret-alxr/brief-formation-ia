import pandas as pd
import pytest

from src.data_pipeline.quarantine import (
    QUARANTINE_COLUMNS,
    empty_quarantine,
    measurement_identifier,
    merge_quarantines,
    quarantine_frame,
)


def test_quarantine_frame_has_stable_column_order():
    record = {name: "value" for name in reversed(QUARANTINE_COLUMNS)}
    assert list(quarantine_frame([record]).columns) == QUARANTINE_COLUMNS


def test_quarantine_frame_rejects_incomplete_record():
    with pytest.raises(ValueError):
        quarantine_frame([{"rule_id": "SEN-DUP-001"}])


def test_measurement_identifier_rebuilds_the_logical_key():
    frame = pd.DataFrame(
        [
            {
                "equipment_id": "EQ-PUMP-001",
                "timestamp": "2026-01-02T00:00:00Z",
                "sensor_name": "vibration_mm_s",
            }
        ]
    )
    assert measurement_identifier(frame).iloc[0] == (
        "EQ-PUMP-001|2026-01-02T00:00:00Z|vibration_mm_s"
    )


def test_measurement_identifier_requires_the_key_columns():
    with pytest.raises(ValueError):
        measurement_identifier(pd.DataFrame([{"equipment_id": "EQ-PUMP-001"}]))


def test_merge_quarantines_keeps_the_common_format():
    record = {name: "value" for name in QUARANTINE_COLUMNS}
    merged = merge_quarantines(empty_quarantine(), quarantine_frame([record]))
    assert list(merged.columns) == QUARANTINE_COLUMNS
    assert len(merged) == 1
