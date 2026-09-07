from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean, pstdev

EXPECTED_UNIT = {
    "vibration_mm_s": "mm/s",
    "temperature_c": "°C",
    "pressure_bar": "bar",
    "current_a": "A",
    "rpm": "rpm",
}
SENTINEL_VALUE = -999.0


def group_windows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["window_id"]].append(row)
    return dict(grouped)


def numeric_summary(rows: list[dict[str, str]]) -> dict[str, float]:
    values: list[float] = []
    missing = 0

    for row in rows:
        try:
            values.append(float(row["value"]))
        except (ValueError, TypeError):
            missing += 1

    return {
        "value_mean": mean(values) if values else 0.0,
        "value_std": pstdev(values) if len(values) > 1 else 0.0,
        "missing_share": missing / len(rows) if rows else 0.0,
    }


def unique_value(rows: list[dict[str, str]], column: str) -> str:
    values = {row[column] for row in rows}

    if len(values) != 1:
        raise ValueError(
            f"La colonne {column!r} contient plusieurs valeurs "
            f"dans une même fenêtre : {sorted(values)}"
        )

    return next(iter(values))


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def rule_signal_features(rows: list[dict[str, str]]) -> dict[str, float]:
    """Traduit les indices déjà connus (baseline M3, `baseline_rules.py`) en
    features numériques par fenêtre, plutôt qu'en verdict binaire figé.

    Un modèle simple peut apprendre à pondérer ces indices (et leurs
    interactions) au lieu de tout traiter comme une règle stricte tout ou
    rien : c'est l'écart attendu entre la baseline par règles et un modèle
    entraîné sur la même information de départ.
    """
    n = len(rows)
    if n == 0:
        return {
            "unit_mismatch_share": 0.0,
            "sentinel_share": 0.0,
            "off_grid_share": 0.0,
            "high_precision_share": 0.0,
            "unreadable_timestamp_share": 0.0,
        }

    unit_mismatch = 0
    sentinel = 0
    off_grid = 0
    high_precision = 0
    unreadable_timestamp = 0

    for row in rows:
        sensor = row.get("sensor_name", "")
        expected_unit = EXPECTED_UNIT.get(sensor)
        if expected_unit is not None and row.get("unit") != expected_unit:
            unit_mismatch += 1

        raw_value = row.get("value", "")
        try:
            numeric = float(raw_value)
        except (ValueError, TypeError):
            numeric = None
        if numeric == SENTINEL_VALUE:
            sentinel += 1
        if isinstance(raw_value, str) and "." in raw_value:
            decimals = raw_value.partition(".")[2]
            if len(decimals) > 2:
                high_precision += 1

        moment = _parse_timestamp(row.get("timestamp", ""))
        if moment is None:
            unreadable_timestamp += 1
        elif moment.minute != 0 or moment.second != 0 or moment.hour % 6:
            off_grid += 1

    return {
        "unit_mismatch_share": unit_mismatch / n,
        "sentinel_share": sentinel / n,
        "off_grid_share": off_grid / n,
        "high_precision_share": high_precision / n,
        "unreadable_timestamp_share": unreadable_timestamp / n,
    }


def build_feature_table(
    rows: list[dict[str, str]],
) -> list[dict[str, float | str]]:
    """Construit une ligne de features par fenêtre."""

    features = []

    for window_id, window_rows in sorted(group_windows(rows).items()):
        entry = {
            "window_id": window_id,
            "equipment_id": unique_value(window_rows, "equipment_id"),
            "sensor_name": unique_value(window_rows, "sensor_name"),
        }
        # Le lot de test ne porte pas `provenance` (étiquette scellée côté
        # formateur) : la clé est omise plutôt que de faire échouer la
        # construction des features, pour que la même fonction serve au
        # lot de calibration et au lot de test.
        if "provenance" in window_rows[0]:
            entry["provenance"] = unique_value(window_rows, "provenance")
        entry.update(numeric_summary(window_rows))
        entry.update(rule_signal_features(window_rows))
        features.append(entry)

    return features