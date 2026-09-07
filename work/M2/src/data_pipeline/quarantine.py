"""Format commun des lignes placées en quarantaine."""

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
