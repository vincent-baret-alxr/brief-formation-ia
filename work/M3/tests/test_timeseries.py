import pandas as pd

from src.data_pipeline.timeseries import (
    duplicated_keys,
    naive_timestamps,
    observed_steps,
    series_overview,
    to_utc,
    window_bounds,
)


def measurements() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("EQ-PUMP-001", "2026-01-02T00:00:00Z", "vibration_mm_s", "2.80", "mm/s"),
            ("EQ-PUMP-001", "2026-01-02T06:00:00Z", "vibration_mm_s", "2.90", "mm/s"),
            ("EQ-PUMP-001", "2026-01-03T00:00:00Z", "vibration_mm_s", "", "mm/s"),
            ("EQ-FAN-002", "2026-01-02 00:00:00", "temperature_c", "58.10", "°C"),
            ("EQ-FAN-002", "2026-01-02 06:00:00", "temperature_c", "331.25", "K"),
        ],
        columns=["equipment_id", "timestamp", "sensor_name", "value", "unit"],
    )


def test_to_utc_accepts_mixed_formats_and_flags_unreadable_values():
    parsed = to_utc(pd.Series(["2026-01-02T00:00:00Z", "2026-01-02 06:00:00", "hier"]))
    assert str(parsed.dt.tz) == "UTC"
    assert parsed.isna().sum() == 1


def test_naive_timestamps_detects_values_without_time_zone():
    flagged = naive_timestamps(pd.Series(["2026-01-02T00:00:00Z", "2026-01-02 06:00:00"]))
    assert flagged.tolist() == [False, True]


def test_duplicated_keys_returns_every_row_sharing_a_key():
    frame = measurements()
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    assert len(duplicated_keys(frame)) == 2


def test_observed_steps_measures_the_gap_between_consecutive_measurements():
    steps = observed_steps(measurements()).dropna().sort_values()
    assert steps.tolist() == [6.0, 6.0, 18.0]


def test_series_overview_describes_each_series():
    overview = series_overview(measurements()).set_index(["equipment_id", "sensor_name"])
    pump = overview.loc[("EQ-PUMP-001", "vibration_mm_s")]
    assert pump["measurements"] == 3
    assert pump["missing_values"] == 1
    assert pump["max_step_hours"] == 18.0
    fan = overview.loc[("EQ-FAN-002", "temperature_c")]
    assert fan["distinct_units"] == 2


def test_window_bounds_uses_the_start_when_the_end_is_missing():
    events = pd.DataFrame(
        [
            {
                "event_id": "EVT-1",
                "start_at": "2026-01-02T12:00:00Z",
                "end_at": "2026-01-02T18:00:00Z",
            },
            {"event_id": "EVT-2", "start_at": "2026-01-03T12:00:00Z", "end_at": ""},
        ]
    )
    bounds = window_bounds(events, before_hours=48, after_hours=24)
    assert bounds.loc[0, "window_start"] == pd.Timestamp("2025-12-31T12:00:00Z")
    assert bounds.loc[1, "window_end"] == pd.Timestamp("2026-01-04T12:00:00Z")
