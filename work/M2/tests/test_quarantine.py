import pytest

from src.data_pipeline.quarantine import QUARANTINE_COLUMNS, quarantine_frame


def test_quarantine_frame_has_stable_column_order():
    record = {name: "value" for name in reversed(QUARANTINE_COLUMNS)}
    assert list(quarantine_frame([record]).columns) == QUARANTINE_COLUMNS


def test_quarantine_frame_rejects_incomplete_record():
    with pytest.raises(ValueError):
        quarantine_frame([{"rule_id": "RULE-1"}])
