"""Format commun des lignes placées en quarantaine.

Le format est celui de M2 : les rejets des quatre sources partagent les mêmes
colonnes et le même vocabulaire de décision. Une mesure n'ayant pas
d'identifiant de ligne, `row_identifier` doit être reconstruit.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


QUARANTINE_COLUMNS = [
    "source_file",
    "row_identifier",
    "rule_id",
    "column",
    "observed_value",
    "reason",
    "decision",
]

DECISIONS = {
    "doublon_supprime",
    "exclue",
    "champ_neutralise",
    "valeur_normalisee",
    "conserve_signale",
    "pseudonymise",
}


def empty_quarantine() -> pd.DataFrame:
    """Crée une quarantaine vide au format demandé par le brief."""
    return pd.DataFrame(columns=QUARANTINE_COLUMNS)


def quarantine_frame(records: Iterable[dict]) -> pd.DataFrame:
    """Valide la présence des colonnes minimales dans les rejets."""
    frame = pd.DataFrame(records)
    missing = [name for name in QUARANTINE_COLUMNS if name not in frame.columns]
    if missing:
        raise ValueError(f"Colonnes de quarantaine manquantes : {missing}")
    return frame.loc[:, QUARANTINE_COLUMNS]


def measurement_identifier(frame: pd.DataFrame) -> pd.Series:
    """Construit un identifiant de mesure à partir de sa clé logique.

    L'identifiant reprend les valeurs telles qu'elles ont été reçues, y compris
    lorsqu'elles sont incohérentes : il doit permettre de retrouver la ligne
    d'origine dans le fichier, pas de la corriger.
    """
    required = ["equipment_id", "timestamp", "sensor_name"]
    missing = [name for name in required if name not in frame.columns]
    if missing:
        raise ValueError(f"Colonnes de clé manquantes : {missing}")
    return (
        frame["equipment_id"].astype("string").fillna("")
        + "|"
        + frame["timestamp"].astype("string").fillna("")
        + "|"
        + frame["sensor_name"].astype("string").fillna("")
    )


def merge_quarantines(*frames: pd.DataFrame) -> pd.DataFrame:
    """Assemble plusieurs quarantaines partielles en une seule table."""
    usable = [frame for frame in frames if not frame.empty]
    if not usable:
        return empty_quarantine()
    merged = pd.concat(usable, ignore_index=True)
    missing = [name for name in QUARANTINE_COLUMNS if name not in merged.columns]
    if missing:
        raise ValueError(f"Colonnes de quarantaine manquantes : {missing}")
    return merged.loc[:, QUARANTINE_COLUMNS]
