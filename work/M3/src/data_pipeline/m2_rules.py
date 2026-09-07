"""Rejeu des règles M2 sur les trois tables ouvertes en M2.

M3 repart de la préparation de référence
``data_pack/2026-S1/reference_runs/m2_for_m3/regles_m2.md`` plutôt que d'une
préparation personnelle (voir ``docs/registre_regles.md`` pour la
justification de ce choix). Chaque fonction ci-dessous réimplémente une règle
du registre de référence à partir de sa condition documentée. La
non-régression est démontrée par ``tests/test_non_regression.py``, qui compare
le résultat obtenu ici aux tables et à la quarantaine de référence.

Une divergence assumée : ``R-MNT-007`` est déclarée ``modifiee`` (voir
``prepare_maintenance``) plutôt que reproduite à l'identique.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from contracts.schemas import (
    CRITICALITIES,
    EQUIPMENT_TYPES,
    EVENT_TYPES,
    INTERVENTION_TYPES,
    MAX_PLAUSIBLE_DOWNTIME_MINUTES,
    PERIOD_BOUNDS,
    SEVERITIES,
)

EMPTY = ""

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+33|0)[\s.-]?[1-9](?:[\s.-]?\d{2}){4}")
# Prénom capitalisé suivi d'une initiale ou d'un nom capitalisé (ex. "Nadia
# B.", "Julien Petit") : motif volontairement étroit, cf. limites de
# `regles_m2.md` ("peut manquer une formulation inhabituelle").
NAME_RE = re.compile(r"\b[A-ZÀ-Ý][a-zà-ÿ]+ [A-ZÀ-Ý](?:[a-zà-ÿ]+\b|\.)")

# Variantes qui ne se ramènent pas au domaine fermé par une simple casse ou un
# espace, mais désignent sans ambiguïté une valeur déjà valide (traduction).
# Trouvée par inspection directe de maintenance_history.csv (MNT-2026S1-0912).
CATEGORY_ALIASES = {"intervention_type": {"correctif": "corrective"}}


def _log(source_file, row_identifier, rule_id, column, observed_value, reason, decision):
    return {
        "source_file": source_file,
        "row_identifier": row_identifier,
        "rule_id": rule_id,
        "column": column,
        "observed_value": observed_value,
        "reason": reason,
        "decision": decision,
    }


def remove_strict_duplicates(
    frame: pd.DataFrame, id_column: str, source_file: str, rule_id: str
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """R-EQ-001 / R-EVT-001 / R-MNT-001 : ligne strictement dupliquée retirée."""
    dup_mask = frame.duplicated(keep="first")
    records = [
        _log(
            source_file,
            row[id_column],
            rule_id,
            id_column,
            row[id_column],
            "Ligne strictement dupliquée",
            "doublon_supprime",
        )
        for _, row in frame.loc[dup_mask].iterrows()
    ]
    return frame.loc[~dup_mask].copy(), records


def exclude_outside_domain(
    frame: pd.DataFrame,
    column: str,
    allowed: set[str],
    id_column: str,
    source_file: str,
    rule_id: str,
    reason: str,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """R-EQ-002 / R-EVT-002 : valeur hors domaine fermé -> ligne exclue."""
    mask = ~frame[column].isin(allowed)
    records = [
        _log(source_file, row[id_column], rule_id, column, row[column], reason, "exclue")
        for _, row in frame.loc[mask].iterrows()
    ]
    return frame.loc[~mask].copy(), records


def normalize_category(
    frame: pd.DataFrame,
    column: str,
    allowed: set[str],
    id_column: str,
    source_file: str,
    rule_id: str,
    reason: str,
) -> tuple[pd.DataFrame, list[dict[str, Any]], pd.Series]:
    """R-EQ-003 / R-EVT-003 / R-MNT-007 : variante de casse/espace normalisée.

    Retourne aussi le masque des lignes normalisées : une valeur dont la
    forme normalisée (espace + casse) ne rejoint aucun domaine connu reste
    inchangée et n'est pas comptée ici (elle est alors hors domaine, pas mal
    formée).
    """
    frame = frame.copy()
    normalized = frame[column].astype(str).str.strip().str.lower()
    aliases = CATEGORY_ALIASES.get(column, {})
    normalized = normalized.replace(aliases)
    needs_fix = (normalized != frame[column]) & normalized.isin(allowed)
    records = [
        _log(
            source_file,
            row[id_column],
            rule_id,
            column,
            row[column],
            reason,
            "valeur_normalisee",
        )
        for _, row in frame.loc[needs_fix].iterrows()
    ]
    frame.loc[needs_fix, column] = normalized.loc[needs_fix]
    return frame, records, needs_fix


def neutralize_field(
    frame: pd.DataFrame,
    column: str,
    mask: pd.Series,
    id_column: str,
    source_file: str,
    rule_id: str,
    reason: str,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Champ vidé et tracé ; la ligne reste dans la table préparée."""
    frame = frame.copy()
    records = [
        _log(source_file, row[id_column], rule_id, column, row[column], reason, "champ_neutralise")
        for _, row in frame.loc[mask].iterrows()
    ]
    frame.loc[mask, column] = pd.NA
    return frame, records


def signal_only(
    frame: pd.DataFrame,
    column: str,
    mask: pd.Series,
    id_column: str,
    source_file: str,
    rule_id: str,
    reason: str,
) -> list[dict[str, Any]]:
    """Ligne conservée telle quelle, anomalie seulement signalée."""
    return [
        _log(source_file, row[id_column], rule_id, column, row[column], reason, "conserve_signale")
        for _, row in frame.loc[mask].iterrows()
    ]


def exclude_unresolved_reference(
    frame: pd.DataFrame,
    column: str,
    known_ids: pd.Series,
    id_column: str,
    source_file: str,
    rule_id: str,
    reason: str,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """R-EVT-005 / R-MNT-002 / R-MNT-003 : référence absente de la table préparée."""
    mask = ~frame[column].isin(set(known_ids))
    records = [
        _log(source_file, row[id_column], rule_id, column, row[column], reason, "exclue")
        for _, row in frame.loc[mask].iterrows()
    ]
    return frame.loc[~mask].copy(), records


def pseudonymize_notes(
    frame: pd.DataFrame, column: str, id_column: str, source_file: str, rule_id: str
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """R-MNT-008 : remplace e-mail, téléphone et nom détectés par un marqueur typé.

    Le marqueur est stable et typé (``[email]``, ``[telephone]``,
    ``[personne]``) plutôt qu'un jeton unique : il indique la nature de
    l'information retirée sans la reconstituer.
    """
    frame = frame.copy()
    records: list[dict[str, Any]] = []
    patterns = [(EMAIL_RE, "[email]", "email"), (PHONE_RE, "[telephone]", "telephone")]

    def _mask(row_id: Any, text: str) -> str:
        found_kinds: list[str] = []
        for pattern, placeholder, kind in patterns:
            if pattern.search(text):
                found_kinds.append(kind)
                text = pattern.sub(placeholder, text)
        # Le nom n'est recherché qu'après retrait de l'e-mail/téléphone pour
        # éviter qu'un fragment numérique ne soit confondu avec un nom.
        if NAME_RE.search(text):
            found_kinds.append("nom")
            text = NAME_RE.sub("[personne]", text)
        if found_kinds:
            records.append(
                _log(
                    source_file,
                    row_id,
                    rule_id,
                    column,
                    "+".join(found_kinds),
                    "Information relative à une personne dans une note libre",
                    "pseudonymise",
                )
            )
        return text

    frame[column] = [
        _mask(row_id, str(text)) for row_id, text in zip(frame[id_column], frame[column])
    ]
    return frame, records


def prepare_equipment(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    source_file = "equipment.csv"
    quarantine: list[dict[str, Any]] = []
    frame = raw.copy()

    # R-EQ-006 se lit sur les valeurs manquantes reçues, avant toute
    # neutralisation ultérieure (R-EQ-004 ne doit pas se faire repérer une
    # deuxième fois par R-EQ-006).
    quarantine += signal_only(
        frame, "manufacturer", frame["manufacturer"].isna(), "equipment_id",
        source_file, "R-EQ-006", "Fabricant manquant",
    )
    quarantine += signal_only(
        frame, "rated_power_kw", frame["rated_power_kw"].isna(), "equipment_id",
        source_file, "R-EQ-006", "Puissance nominale manquante",
    )

    frame, records = remove_strict_duplicates(frame, "equipment_id", source_file, "R-EQ-001")
    quarantine += records

    frame, records = exclude_outside_domain(
        frame, "criticality", CRITICALITIES, "equipment_id", source_file, "R-EQ-002",
        "Criticité hors domaine",
    )
    quarantine += records

    frame, records, _ = normalize_category(
        frame, "equipment_type", EQUIPMENT_TYPES, "equipment_id", source_file, "R-EQ-003",
        "Catégorie non normalisée",
    )
    quarantine += records

    mask_power = frame["rated_power_kw"].notna() & (frame["rated_power_kw"] <= 0)
    frame, records = neutralize_field(
        frame, "rated_power_kw", mask_power, "equipment_id", source_file, "R-EQ-004",
        "Puissance nominale nulle ou négative",
    )
    quarantine += records

    period_end = PERIOD_BOUNDS["2026-S1"][1]
    commissioning = pd.to_datetime(frame["commissioning_date"], errors="coerce")
    mask_date = frame["commissioning_date"].notna() & (
        commissioning.dt.date > period_end
    )
    frame, records = neutralize_field(
        frame, "commissioning_date", mask_date, "equipment_id", source_file, "R-EQ-005",
        "Date de mise en service absente ou postérieure à la période",
    )
    quarantine += records

    return frame, quarantine


def prepare_events(
    raw: pd.DataFrame, prepared_equipment: pd.DataFrame
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    source_file = "events.csv"
    quarantine: list[dict[str, Any]] = []
    frame = raw.copy()

    frame, records = remove_strict_duplicates(frame, "event_id", source_file, "R-EVT-001")
    quarantine += records

    frame, records = exclude_outside_domain(
        frame, "severity", SEVERITIES, "event_id", source_file, "R-EVT-002",
        "Sévérité hors domaine",
    )
    quarantine += records

    frame, records, _ = normalize_category(
        frame, "event_type", EVENT_TYPES, "event_id", source_file, "R-EVT-003",
        "Type d'événement non normalisé",
    )
    quarantine += records

    start = pd.to_datetime(frame["start_at"], errors="coerce", utc=True)
    end = pd.to_datetime(frame["end_at"], errors="coerce", utc=True)
    mask_end = frame["end_at"].notna() & (end < start)
    frame, records = neutralize_field(
        frame, "end_at", mask_end, "event_id", source_file, "R-EVT-004",
        "Fin antérieure au début",
    )
    quarantine += records

    frame, records = exclude_unresolved_reference(
        frame, "equipment_id", prepared_equipment["equipment_id"], "event_id",
        source_file, "R-EVT-005", "Équipement référencé absent de la table préparée",
    )
    quarantine += records

    return frame, quarantine


def prepare_maintenance(
    raw: pd.DataFrame,
    prepared_equipment: pd.DataFrame,
    prepared_events: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    source_file = "maintenance_history.csv"
    quarantine: list[dict[str, Any]] = []
    frame = raw.copy()

    frame, records = remove_strict_duplicates(frame, "maintenance_id", source_file, "R-MNT-001")
    quarantine += records

    frame, records = exclude_unresolved_reference(
        frame, "event_id", prepared_events["event_id"], "maintenance_id",
        source_file, "R-MNT-002", "Événement référencé absent de la table préparée",
    )
    quarantine += records

    frame, records = exclude_unresolved_reference(
        frame, "equipment_id", prepared_equipment["equipment_id"], "maintenance_id",
        source_file, "R-MNT-003", "Équipement référencé absent de la table préparée",
    )
    quarantine += records

    opened = pd.to_datetime(frame["opened_at"], errors="coerce", utc=True)
    closed = pd.to_datetime(frame["closed_at"], errors="coerce", utc=True)
    mask_closed = frame["closed_at"].notna() & (closed < opened)
    frame, records = neutralize_field(
        frame, "closed_at", mask_closed, "maintenance_id", source_file, "R-MNT-004",
        "Clôture antérieure à l'ouverture",
    )
    quarantine += records

    mask_negative_downtime = frame["downtime_minutes"] < 0
    quarantine += [
        _log(
            source_file, row["maintenance_id"], "R-MNT-005", "downtime_minutes",
            row["downtime_minutes"], "Durée d'arrêt négative ou illisible", "exclue",
        )
        for _, row in frame.loc[mask_negative_downtime].iterrows()
    ]
    frame = frame.loc[~mask_negative_downtime].copy()

    mask_sentinel_downtime = frame["downtime_minutes"] > MAX_PLAUSIBLE_DOWNTIME_MINUTES
    quarantine += signal_only(
        frame, "downtime_minutes", mask_sentinel_downtime, "maintenance_id", source_file,
        "R-MNT-005", "Durée d'arrêt supérieure à quatorze jours, expertise métier requise",
    )

    mask_cost = frame["parts_cost_eur"].notna() & (frame["parts_cost_eur"] < 0)
    frame, records = neutralize_field(
        frame, "parts_cost_eur", mask_cost, "maintenance_id", source_file, "R-MNT-006",
        "Coût de pièces négatif",
    )
    quarantine += records

    # R-MNT-007 est déclarée MODIFIEE pour M3 (voir docs/registre_regles.md) :
    # le registre de référence exclut MNT-2026S1-0912 après l'avoir
    # normalisée ("Correctif" -> "corrective", valeur pourtant valide),
    # alors que R-EVT-003 traite une variante analogue ("Incident " ->
    # "incident") par simple normalisation, ligne conservée. Ce traitement
    # différent d'une même famille d'anomalie n'est pas justifié dans
    # `regles_m2.md`. M3 aligne R-MNT-007 sur R-EVT-003 : normalisation puis
    # conservation, sans exclusion, tant que la valeur normalisée appartient
    # au domaine fermé.
    frame, records, _ = normalize_category(
        frame, "intervention_type", INTERVENTION_TYPES, "maintenance_id", source_file,
        "R-MNT-007", "Type d'intervention non normalisé",
    )
    quarantine += records

    frame, records = pseudonymize_notes(
        frame, "work_order_note", "maintenance_id", source_file, "R-MNT-008"
    )
    quarantine += records

    return frame, quarantine
