"""Contrôles simples réutilisables dans le pipeline M3.

Ces contrôles sont ceux de M2. Ils sont conservés tels quels : une règle héritée
qui change de comportement sans trace est un défaut de traçabilité.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def missing_required_columns(
    frame: pd.DataFrame, required_columns: Iterable[str]
) -> list[str]:
    """Retourne les colonnes obligatoires absentes, dans un ordre stable."""
    return sorted(set(required_columns) - set(frame.columns))


def unknown_categories(frame: pd.DataFrame, column: str, allowed: Iterable[str]) -> list[str]:
    """Retourne les valeurs de `column` hors du domaine fermé attendu."""
    if column not in frame.columns:
        raise ValueError(f"Colonne absente : {column}")
    observed = set(frame[column].dropna().unique())
    return sorted(observed - set(allowed))


def unresolved_references(
    frame: pd.DataFrame, column: str, known_values: Iterable[str]
) -> list[str]:
    """Retourne les valeurs de `column` sans correspondance dans la table cible."""
    if column not in frame.columns:
        raise ValueError(f"Colonne absente : {column}")
    observed = set(frame[column].dropna().unique())
    return sorted(observed - set(known_values))
