"""Contrôles simples réutilisables dans le pipeline M2."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def missing_required_columns(
    frame: pd.DataFrame, required_columns: Iterable[str]
) -> list[str]:
    """Retourne les colonnes obligatoires absentes, dans un ordre stable."""
    return sorted(set(required_columns) - set(frame.columns))

