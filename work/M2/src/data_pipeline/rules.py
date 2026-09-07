"""Règles métier et contrôles rejouables du brief M2.

Ce module complète les schémas Pandera de ``contracts.schemas`` par les
contrôles qu'un schéma par table ne peut pas exprimer : intégrité
référentielle entre tables, doublons stricts et détection d'informations
relatives à des personnes dans les notes libres.

Chaque fonction retourne des enregistrements au format de
``quarantine.QUARANTINE_COLUMNS`` ou de ``CORRECTION_COLUMNS`` : la donnée
observée, la règle appliquée et la raison sont toujours tracées.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

import pandas as pd

CORRECTION_COLUMNS = [
    "source_file",
    "row_identifier",
    "rule_id",
    "column",
    "before",
    "after",
    "reason",
]

ID_COLUMNS = {
    "equipment": "equipment_id",
    "events": "event_id",
    "maintenance": "maintenance_id",
}

DATE_COLUMNS = {
    "equipment": ["commissioning_date"],
    "events": ["start_at", "end_at"],
    "maintenance": ["opened_at", "closed_at"],
}

# Variantes observées dans les fichiers reçus qui désignent sans ambiguïté
# une valeur déjà présente dans le domaine fermé du contrat (contracts.schemas).
# La correction est appliquée et tracée ; aucune valeur n'est devinée.
CATEGORY_FIXES = {
    "equipment": {"equipment_type": {"Pump": "pump"}},
    "events": {"event_type": {"Incident": "incident"}},
    "maintenance": {"intervention_type": {"Correctif": "corrective"}},
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+33|0)[\s.-]?[1-9](?:[\s.-]?\d{2}){4}")
PII_MASK = "[donnée personnelle masquée]"


def parse_dates(frame: pd.DataFrame, columns: Iterable[str], utc: bool = False) -> pd.DataFrame:
    """Retourne une copie avec les colonnes de dates converties en datetime.

    Les valeurs non convertibles deviennent ``NaT`` et sont donc capturées par
    la contrainte ``nullable=False`` des schémas Pandera plutôt qu'ignorées
    silencieusement.
    """
    frame = frame.copy()
    for column in columns:
        frame[column] = pd.to_datetime(frame[column], errors="coerce", utc=utc)
    return frame


def apply_category_fixes(
    frame: pd.DataFrame, source_file: str, id_column: str
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Corrige les variantes de casse/orthographe listées dans CATEGORY_FIXES.

    Retourne le frame corrigé et le journal des corrections (avant/après).
    """
    frame = frame.copy()
    records: list[dict[str, Any]] = []
    fixes = CATEGORY_FIXES.get(source_file.split(".")[0], {})
    for column, mapping in fixes.items():
        if column not in frame.columns:
            continue
        normalized = frame[column].astype(str).str.strip()
        for wrong, right in mapping.items():
            mask = normalized == wrong
            for row_id, before in zip(frame.loc[mask, id_column], frame.loc[mask, column]):
                records.append(
                    {
                        "source_file": source_file,
                        "row_identifier": row_id,
                        "rule_id": f"{column.upper()}_CATEGORY_NORMALIZED",
                        "column": column,
                        "before": before,
                        "after": right,
                        "reason": (
                            f"Variante de casse/espace de '{right}' sans ambiguïté métier."
                        ),
                    }
                )
            frame.loc[mask, column] = right
    return frame, records


def mask_pii_in_notes(
    frame: pd.DataFrame, source_file: str, id_column: str, column: str = "work_order_note"
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Masque les adresses e-mail et numéros de téléphone détectés dans ``column``.

    Les identifiants techniques (``equipment_id``, ``event_id``, ...) ne sont
    pas concernés par ces expressions et restent inchangés.
    """
    frame = frame.copy()
    records: list[dict[str, Any]] = []
    if column not in frame.columns:
        return frame, records

    def _mask(row_id: Any, text: str) -> str:
        found = EMAIL_RE.findall(text) + PHONE_RE.findall(text)
        if not found:
            return text
        for match in found:
            records.append(
                {
                    "source_file": source_file,
                    "row_identifier": row_id,
                    "rule_id": "PII_DETECTED_IN_NOTE",
                    "column": column,
                    "before": match,
                    "after": PII_MASK,
                    "reason": "Adresse e-mail ou numéro de téléphone détecté dans un champ libre.",
                }
            )
        text = EMAIL_RE.sub(PII_MASK, text)
        text = PHONE_RE.sub(PII_MASK, text)
        return text

    frame[column] = [
        _mask(row_id, str(text)) for row_id, text in zip(frame[id_column], frame[column])
    ]
    return frame, records


def duplicate_row_mask(frame: pd.DataFrame) -> pd.Series:
    """Retourne un masque booléen des lignes strictement dupliquées (hors 1re occurrence)."""
    return frame.duplicated(keep="first")


def referential_breaks(
    child: pd.DataFrame, child_column: str, parent_ids: pd.Series
) -> pd.Series:
    """Retourne un masque des lignes dont la clé étrangère n'existe pas chez le parent."""
    return ~child[child_column].isin(set(parent_ids))


def quarantine_records_from_mask(
    frame: pd.DataFrame,
    mask: pd.Series,
    source_file: str,
    id_column: str,
    rule_id: str,
    column: str,
    reason: str,
    decision: str,
) -> list[dict[str, Any]]:
    """Construit des enregistrements de quarantaine pour les lignes signalées par ``mask``."""
    subset = frame.loc[mask]
    return [
        {
            "source_file": source_file,
            "row_identifier": row[id_column],
            "rule_id": rule_id,
            "column": column,
            "observed_value": row[column] if column in row else row[id_column],
            "reason": reason,
            "decision": decision,
        }
        for _, row in subset.iterrows()
    ]


def _sanitize_rule_id(text: str) -> str:
    """Normalise un libellé libre en identifiant de règle stable et lisible."""
    upper = re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_").upper()
    return re.sub(r"_+", "_", upper)


def schema_failures_to_quarantine(
    failure_cases: pd.DataFrame,
    frame: pd.DataFrame,
    source_file: str,
    id_column: str,
    decision: str = "a_examiner",
) -> list[dict[str, Any]]:
    """Convertit les ``failure_cases`` Pandera (mode lazy) au format de quarantaine.

    Pandera référence les lignes par position (``index``) : on retrouve
    l'identifiant métier de la ligne pour rester cohérent avec les autres
    règles, dont les identifiants techniques.
    """
    # Un contrôle défini au niveau du DataFrame (colonnes croisées, ex. dates
    # de début/fin) produit une ligne de `failure_cases` par colonne du
    # tableau pour la même ligne en échec : on la ramène à un seul
    # enregistrement par (ligne, contrôle) pour ne pas gonfler la quarantaine.
    is_row_level = failure_cases["schema_context"] == "DataFrameSchema"
    row_level = failure_cases.loc[is_row_level].drop_duplicates(subset=["index", "check"])
    column_level = failure_cases.loc[~is_row_level]
    deduped = pd.concat([column_level, row_level], ignore_index=True)

    records: list[dict[str, Any]] = []
    for _, failure in deduped.iterrows():
        row_index = failure["index"]
        if row_index is not None and row_index in frame.index:
            row_identifier = frame.loc[row_index, id_column]
        else:
            row_identifier = None
        if failure["schema_context"] == "DataFrameSchema":
            column = "__ligne__"
            observed_value = row_identifier
        else:
            column = failure["column"]
            observed_value = failure["failure_case"]
        rule_id = _sanitize_rule_id(f"{column}_{failure['check']}")
        records.append(
            {
                "source_file": source_file,
                "row_identifier": row_identifier,
                "rule_id": rule_id,
                "column": column,
                "observed_value": observed_value,
                "reason": f"Contrainte de schéma non respectée : {failure['check']}",
                "decision": decision,
            }
        )
    return records
