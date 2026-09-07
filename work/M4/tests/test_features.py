from src.features import build_feature_table, rule_signal_features


def _row(**overrides):
    row = {
        "window_id": "W1",
        "equipment_id": "EQ1",
        "sensor_name": "temperature_c",
        "timestamp": "2026-01-01T00:00:00Z",
        "value": "1.0",
        "unit": "°C",
        "provenance": "réelle",
    }
    row.update(overrides)
    return row


def test_feature_table_has_one_row_per_window():
    rows = [_row(value="1.0"), _row(value="3.0")]

    table = build_feature_table(rows)
    assert len(table) == 1
    entry = table[0]
    assert entry["window_id"] == "W1"
    assert entry["equipment_id"] == "EQ1"
    assert entry["sensor_name"] == "temperature_c"
    assert entry["provenance"] == "réelle"
    assert entry["value_mean"] == 2.0
    assert entry["value_std"] == 1.0
    assert entry["missing_share"] == 0.0
    assert entry["unit_mismatch_share"] == 0.0
    assert entry["sentinel_share"] == 0.0


def test_feature_table_omits_provenance_when_absent_from_the_test_lot():
    rows = [
        {
            "window_id": "W1",
            "equipment_id": "EQ1",
            "sensor_name": "temperature_c",
            "timestamp": "2026-01-01T00:00:00Z",
            "value": "1.0",
            "unit": "°C",
        }
    ]
    entry = build_feature_table(rows)[0]
    assert "provenance" not in entry


def test_rule_signal_features_flags_unit_mismatch():
    rows = [_row(unit="K"), _row(unit="°C")]
    signal = rule_signal_features(rows)
    assert signal["unit_mismatch_share"] == 0.5


def test_rule_signal_features_flags_sentinel_value():
    rows = [_row(value="-999.0"), _row(value="20.0")]
    signal = rule_signal_features(rows)
    assert signal["sentinel_share"] == 0.5


def test_rule_signal_features_flags_off_grid_timestamp():
    rows = [_row(timestamp="2026-01-01T00:00:00Z"), _row(timestamp="2026-01-01T01:00:00Z")]
    signal = rule_signal_features(rows)
    assert signal["off_grid_share"] == 0.5


def test_rule_signal_features_flags_high_precision_value():
    rows = [_row(value="1.234"), _row(value="1.20")]
    signal = rule_signal_features(rows)
    assert signal["high_precision_share"] == 0.5


def test_rule_signal_features_handles_empty_window():
    assert rule_signal_features([])["sentinel_share"] == 0.0
