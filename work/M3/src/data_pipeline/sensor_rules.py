"""Règles temporelles introduites en M3 pour ``sensor_readings.csv``.

Nouvelles règles, identifiants ``SEN-*`` (aucune de ces conditions n'existait
en M2). Chaque fonction retourne la table travaillée et les enregistrements
de quarantaine correspondants, au format unifié de ``quarantine.py``.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from contracts.schemas import (
    ANNOUNCED_PERIOD,
    PERIOD_BOUNDS,
    SENSOR_UNITS,
    UNIT_CONVERSIONS,
)
from src.data_pipeline.timeseries import naive_timestamps, to_utc

SOURCE_FILE = "sensor_readings.csv"
ID_COLUMNS = ["equipment_id", "timestamp", "sensor_name"]

# Valeur trouvée à l'identique sur les cinq capteurs (current_a, pressure_bar,
# rpm, temperature_c, vibration_mm_s) : aucune de ces grandeurs ne peut être
# négative, -999 est une valeur sentinelle d'origine capteur/export, pas une
# mesure.
SENTINEL_VALUE = -999.0

# Nom de capteur mal formé mais sans ambiguïté sur le domaine visé (casse,
# espace) : trouvé par inspection directe ("TEMPERATURE_C " -> temperature_c).
SENSOR_NAME_ALIASES = {name.strip().lower(): name for name in SENSOR_UNITS}


def _log(row_identifier, rule_id, column, observed_value, reason, decision):
    return {
        "source_file": SOURCE_FILE,
        "row_identifier": row_identifier,
        "rule_id": rule_id,
        "column": column,
        "observed_value": observed_value,
        "reason": reason,
        "decision": decision,
    }


def _row_id(row: pd.Series) -> str:
    return f"{row['equipment_id']}|{row['timestamp']}|{row['sensor_name']}"


def normalize_sensor_name(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """SEN-NAME-001 : variante de casse/espace de ``sensor_name`` normalisée."""
    frame = frame.copy()
    stripped_lower = frame["sensor_name"].astype(str).str.strip().str.lower()
    needs_fix = (stripped_lower != frame["sensor_name"]) & stripped_lower.isin(SENSOR_NAME_ALIASES)
    records = [
        _log(
            _row_id(row), "SEN-NAME-001", "sensor_name", row["sensor_name"],
            "Nom de capteur non normalisé (casse ou espace)", "valeur_normalisee",
        )
        for _, row in frame.loc[needs_fix].iterrows()
    ]
    frame.loc[needs_fix, "sensor_name"] = stripped_lower.loc[needs_fix]
    return frame, records


def normalize_units(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """SEN-UNIT-001 : convertit les mesures dans une unité non canonique.

    Trouvé par inspection directe : une partie des relevés de
    ``temperature_c`` est exprimée en kelvin, une partie des relevés de
    ``pressure_bar`` en kilopascal. La valeur est convertie vers l'unité
    canonique du capteur (``contracts.schemas.SENSOR_UNITS``) ; la ligne est
    conservée.
    """
    frame = frame.copy()
    records: list[dict[str, Any]] = []
    for sensor_name, conversions in UNIT_CONVERSIONS.items():
        canonical_unit = SENSOR_UNITS[sensor_name]
        for unit, convert in conversions.items():
            mask = (frame["sensor_name"] == sensor_name) & (frame["unit"] == unit)
            for _, row in frame.loc[mask].iterrows():
                records.append(
                    _log(
                        _row_id(row), "SEN-UNIT-001", "value",
                        f"{row['value']} {unit}",
                        f"Unité {unit} non canonique pour {sensor_name} (attendue : {canonical_unit})",
                        "valeur_normalisee",
                    )
                )
            frame.loc[mask, "value"] = convert(frame.loc[mask, "value"])
            frame.loc[mask, "unit"] = canonical_unit
    return frame, records


def normalize_timestamps(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """SEN-TZ-001 : horodatage sans fuseau, converti en supposant UTC.

    L'hypothèse UTC est celle documentée par ``timeseries.to_utc`` ; elle est
    tracée ici plutôt qu'appliquée silencieusement, conformément aux règles
    de travail du starter.
    """
    frame = frame.copy()
    naive_mask = naive_timestamps(frame["timestamp"])
    records = [
        _log(
            _row_id(row), "SEN-TZ-001", "timestamp", row["timestamp"],
            "Horodatage sans fuseau, UTC supposé", "valeur_normalisee",
        )
        for _, row in frame.loc[naive_mask].iterrows()
    ]
    frame["timestamp"] = to_utc(frame["timestamp"])
    return frame, records


def exclude_sentinel_values(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """SEN-RANGE-001 (sentinelle) : valeur -999 impossible pour toute grandeur mesurée ici."""
    mask = frame["value"] == SENTINEL_VALUE
    records = [
        _log(_row_id(row), "SEN-RANGE-001", "value", row["value"], "Valeur sentinelle -999", "exclue")
        for _, row in frame.loc[mask].iterrows()
    ]
    return frame.loc[~mask].copy(), records


def exclude_out_of_range_values(
    frame: pd.DataFrame, ranges: dict[str, tuple[float, float]]
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """SEN-RANGE-001 (plage) : valeur hors plage physique plausible, hors sentinelle."""
    lower = frame["sensor_name"].map(lambda name: ranges.get(name, (float("-inf"), float("inf")))[0])
    upper = frame["sensor_name"].map(lambda name: ranges.get(name, (float("-inf"), float("inf")))[1])
    mask = frame["value"].notna() & ~frame["value"].between(lower, upper)
    records = [
        _log(
            _row_id(row), "SEN-RANGE-001", "value", row["value"],
            "Valeur hors plage physique plausible pour ce capteur", "exclue",
        )
        for _, row in frame.loc[mask].iterrows()
    ]
    return frame.loc[~mask].copy(), records


def signal_missing_values(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """SEN-NULL-001 : valeur manquante signalée, ligne conservée."""
    mask = frame["value"].isna()
    return [
        _log(_row_id(row), "SEN-NULL-001", "value", "", "Mesure non relevée", "conserve_signale")
        for _, row in frame.loc[mask].iterrows()
    ]


def exclude_out_of_announced_period(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """SEN-PERIOD-001 : ligne hors de la période annoncée pour cette livraison.

    Ce n'est pas une erreur (les mesures existent réellement) mais un
    problème de périmètre : la livraison ``2026-S1`` annonce la période
    ``2026-S1`` ; toute autre valeur de ``period`` est hors du périmètre
    couvert par ce contrôle et doit être retraitée avec la livraison
    correspondante, pas mélangée à celle-ci.
    """
    mask = frame["period"] != ANNOUNCED_PERIOD
    records = [
        _log(
            _row_id(row), "SEN-PERIOD-001", "period", row["period"],
            f"Période hors périmètre annoncé ({ANNOUNCED_PERIOD})", "exclue",
        )
        for _, row in frame.loc[mask].iterrows()
    ]
    return frame.loc[~mask].copy(), records


def exclude_unknown_equipment(
    frame: pd.DataFrame, known_equipment_ids: pd.Series
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """SEN-REF-001 : mesure rattachée à un équipement absent de la table préparée."""
    mask = ~frame["equipment_id"].isin(set(known_equipment_ids))
    records = [
        _log(
            _row_id(row), "SEN-REF-001", "equipment_id", row["equipment_id"],
            "Équipement référencé absent de la table préparée", "exclue",
        )
        for _, row in frame.loc[mask].iterrows()
    ]
    return frame.loc[~mask].copy(), records


def resolve_duplicate_keys(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """SEN-KEY-001 : arbitrage des doublons de la clé logique.

    Un doublon strict (même clé, même valeur) est un enregistrement répété :
    la copie surnuméraire est retirée. Un doublon de clé porteur de deux
    valeurs différentes ne peut pas être arbitré automatiquement (aucune
    trace ne dit laquelle des deux mesures est la bonne) : les deux lignes
    sont exclues et signalées pour reprise auprès du fournisseur de la
    donnée, conformément aux critères bloquants du brief (« doublon de clé
    résolu sans arbitrage tracé »).
    """
    frame = frame.copy()
    key_dup_mask = frame.duplicated(subset=ID_COLUMNS, keep=False)
    if not key_dup_mask.any():
        return frame, []

    strict_dup_mask = frame.duplicated(keep=False) & key_dup_mask
    divergent_mask = key_dup_mask & ~strict_dup_mask

    records: list[dict[str, Any]] = []
    strict_extra_mask = frame.duplicated(keep="first") & strict_dup_mask
    for _, row in frame.loc[strict_extra_mask].iterrows():
        records.append(
            _log(_row_id(row), "SEN-KEY-001", "value", row["value"], "Doublon strict de la clé logique", "doublon_supprime")
        )

    for _, row in frame.loc[divergent_mask].iterrows():
        records.append(
            _log(
                _row_id(row), "SEN-KEY-001", "value", row["value"],
                "Doublon de clé porteur de deux valeurs différentes, non arbitrable automatiquement",
                "exclue",
            )
        )

    frame = frame.loc[~(strict_extra_mask | divergent_mask)].copy()
    return frame, records


def flag_frozen_runs(frame: pd.DataFrame, min_run: int = 6) -> pd.DataFrame:
    """Diagnostic (non bloquant) : repère les séquences de valeurs consécutives identiques.

    Une valeur figée n'est pas exclue automatiquement : elle peut être un
    comportement de capteur bloqué comme une mesure réelle stable (cf. axe 3
    du brief). Cette fonction produit une table d'observations pour le
    diagnostic, elle ne modifie pas les données.
    """
    working = frame.dropna(subset=["value"]).sort_values(ID_COLUMNS[:1] + ["sensor_name", "timestamp"]).copy()
    working["_same_as_prev"] = working.groupby(["equipment_id", "sensor_name"])["value"].diff().eq(0)
    working["_run_id"] = (~working["_same_as_prev"]).groupby(
        [working["equipment_id"], working["sensor_name"]]
    ).cumsum()
    run_lengths = (
        working.groupby(["equipment_id", "sensor_name", "_run_id"])
        .agg(run_length=("value", "size"), value=("value", "first"),
             first_seen=("timestamp", "min"), last_seen=("timestamp", "max"))
        .reset_index(drop=False)
    )
    frozen = run_lengths.loc[run_lengths["run_length"] >= min_run].drop(columns=["_run_id"])
    return frozen.sort_values("run_length", ascending=False).reset_index(drop=True)
