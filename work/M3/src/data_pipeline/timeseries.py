"""Primitives descriptives pour une source temporelle.

Ces fonctions décrivent ce que contient la source. Elles ne décident rien : le
seuil d'acceptation d'un écart d'échantillonnage, le sort d'un doublon de clé ou
la fenêtre de rapprochement relèvent du brief, pas du starter.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


MEASUREMENT_KEY = ["equipment_id", "timestamp", "sensor_name"]


def to_utc(values: pd.Series) -> pd.Series:
    """Convertit des horodatages hétérogènes en instants UTC.

    Les valeurs illisibles deviennent `NaT` au lieu d'interrompre le traitement :
    elles doivent être comptées et tracées. Une valeur sans fuseau est
    interprétée comme UTC ; c'est une hypothèse, à confirmer ou à écarter.
    """
    parsed = pd.to_datetime(values, errors="coerce", utc=True, format="mixed")
    return parsed


def naive_timestamps(values: pd.Series) -> pd.Series:
    """Signale les horodatages écrits sans indication de fuseau."""
    text = values.astype("string")
    has_zone = text.str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", regex=True, na=False)
    return ~has_zone & text.notna()


def duplicated_keys(
    frame: pd.DataFrame, key_columns: Iterable[str] = MEASUREMENT_KEY
) -> pd.DataFrame:
    """Retourne les lignes dont la clé apparaît plusieurs fois.

    Le résultat mélange volontairement doublons stricts et doublons porteurs de
    valeurs différentes : les distinguer et les arbitrer fait partie du travail.
    """
    columns = list(key_columns)
    mask = frame.duplicated(subset=columns, keep=False)
    return frame.loc[mask].sort_values(columns)


def observed_steps(
    frame: pd.DataFrame,
    timestamp_column: str = "timestamp",
    group_columns: Iterable[str] = ("equipment_id", "sensor_name"),
) -> pd.Series:
    """Écarts entre mesures consécutives, en heures, série par série."""
    columns = list(group_columns)
    working = frame.loc[:, columns + [timestamp_column]].copy()
    working[timestamp_column] = to_utc(working[timestamp_column])
    working = working.dropna(subset=[timestamp_column])
    working = working.sort_values(columns + [timestamp_column])
    deltas = working.groupby(columns, observed=True)[timestamp_column].diff()
    return deltas.dt.total_seconds() / 3600


def series_overview(
    frame: pd.DataFrame,
    timestamp_column: str = "timestamp",
    value_column: str = "value",
    group_columns: Iterable[str] = ("equipment_id", "sensor_name"),
) -> pd.DataFrame:
    """Décrit chaque série : volume, période couverte, pas et complétude."""
    columns = list(group_columns)
    working = frame.loc[:, columns + [timestamp_column, value_column, "unit"]].copy()
    working[timestamp_column] = to_utc(working[timestamp_column])
    working[value_column] = pd.to_numeric(working[value_column], errors="coerce")
    working["_step"] = observed_steps(frame, timestamp_column, columns).reindex(
        working.index
    )

    grouped = working.groupby(columns, observed=True)
    overview = grouped.agg(
        measurements=(timestamp_column, "size"),
        first_seen=(timestamp_column, "min"),
        last_seen=(timestamp_column, "max"),
        unreadable_timestamps=(timestamp_column, lambda values: int(values.isna().sum())),
        missing_values=(value_column, lambda values: int(values.isna().sum())),
        distinct_units=("unit", "nunique"),
        median_step_hours=("_step", "median"),
        max_step_hours=("_step", "max"),
    )
    return overview.reset_index()


def window_bounds(
    events: pd.DataFrame,
    before_hours: float,
    after_hours: float,
    start_column: str = "start_at",
    end_column: str = "end_at",
) -> pd.DataFrame:
    """Construit les bornes d'observation autour de chaque événement.

    La fenêtre est un paramètre du brief : `before_hours` et `after_hours`
    doivent être choisis et justifiés. Un événement sans fin renseignée voit sa
    borne haute calculée à partir de son début.
    """
    working = events.copy()
    start = to_utc(working[start_column])
    end = to_utc(working[end_column]).fillna(start)
    working["window_start"] = start - pd.Timedelta(hours=before_hours)
    working["window_end"] = end + pd.Timedelta(hours=after_hours)
    return working
