from pathlib import Path

from src.features import build_feature_table
from src.model_eval import build_matrix, window_level_baseline


def _window_rows(window_id, equipment_id, sensor_name, provenance, values):
    return [
        {
            "window_id": window_id,
            "equipment_id": equipment_id,
            "sensor_name": sensor_name,
            "timestamp": f"2026-01-01T{6 * i:02d}:00:00Z",
            "value": str(v),
            "unit": "mm/s",
            "provenance": provenance,
        }
        for i, v in enumerate(values)
    ]


def test_build_matrix_encodes_positive_label_as_one():
    rows = _window_rows("W1", "EQ-1", "vibration_mm_s", "fabriquée", [1.0, 2.0]) + _window_rows(
        "W2", "EQ-2", "vibration_mm_s", "réelle", [1.0, 2.0]
    )
    table = build_feature_table(rows)
    x, y, groups, window_ids = build_matrix(table)
    assert y.tolist() == [1, 0] or y.tolist() == [0, 1]
    label_by_window = dict(zip(window_ids, y.tolist()))
    assert label_by_window["W1"] == 1
    assert label_by_window["W2"] == 0
    assert set(groups) == {"EQ-1", "EQ-2"}


def test_build_matrix_handles_missing_provenance_for_the_test_lot():
    rows = _window_rows("W1", "EQ-1", "vibration_mm_s", None, [1.0, 2.0])
    for row in rows:
        del row["provenance"]
    table = build_feature_table(rows)
    _, y, _, _ = build_matrix(table)
    assert y is None


def test_window_level_baseline_uses_majority_vote_per_window(tmp_path: Path):
    predictions = tmp_path / "baseline_predictions.csv"
    predictions.write_text(
        "window_id,provenance,prediction\n"
        "W1,fabriquée,fabriquée\n"
        "W1,fabriquée,fabriquée\n"
        "W1,fabriquée,réelle\n"
        "W2,réelle,réelle\n"
        "W2,réelle,réelle\n",
        encoding="utf-8",
    )
    result = window_level_baseline(predictions)
    assert result["n_windows"] == 2
    assert result["confusion_matrix"] == {"tn": 1, "fp": 0, "fn": 0, "tp": 1}
