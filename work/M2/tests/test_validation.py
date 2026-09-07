import pandas as pd

from src.data_pipeline.validation import missing_required_columns


def test_valid_frame_has_no_missing_required_column():
    frame = pd.DataFrame([{"equipment_id": "EQ-001", "site_id": "SITE-A"}])
    assert missing_required_columns(frame, ["equipment_id", "site_id"]) == []


def test_invalid_frame_reports_missing_required_column():
    frame = pd.DataFrame([{"equipment_id": "EQ-001"}])
    assert missing_required_columns(frame, ["equipment_id", "site_id"]) == ["site_id"]

