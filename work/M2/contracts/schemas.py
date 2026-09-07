"""Contrats de données M2.

Les domaines fermés sont fournis pour éviter la ressaisie. Les schémas
Pandera ci-dessous encodent les règles métier justifiées dans
``docs/diagnostic_donnees.md`` : un type et une contrainte par colonne, plus
quelques contrôles inter-colonnes (cohérence des dates). Les schémas sont
volontairement stricts : ils décrivent la donnée *cible* après nettoyage, pas
les fichiers bruts reçus (qui contiennent des anomalies pédagogiques connues).
Faire échouer ``schema.validate(df, lazy=True)`` sur les données brutes est
donc attendu ; c'est ce que le pipeline utilise pour lister les anomalies.
"""

from __future__ import annotations

import pandas as pd
import pandera.pandas as pa

SEVERITIES = {"low", "medium", "high", "critical"}
CRITICALITIES = {"low", "medium", "high", "critical"}
EVENT_TYPES = {"incident", "intervention", "observation", "alert"}
INTERVENTION_TYPES = {
    "inspection",
    "corrective",
    "preventive",
    "calibration",
    "replacement",
}
OUTCOMES = {
    "resolved",
    "monitoring",
    "parts_ordered",
    "no_fault_found",
    "follow_up_required",
}
EQUIPMENT_TYPES = {
    "electrical_cabinet",
    "chiller",
    "compressor",
    "conveyor",
    "dryer",
    "fan",
    "gearbox",
    "lift",
    "mixer",
    "motor",
    "oven",
    "packaging_machine",
    "press",
    "pump",
    "robot",
    "sensor",
    "steam_unit",
    "valve",
}
SITE_IDS = {"SITE-SUD", "SITE-EST", "SITE-NORD", "SITE-OUEST"}

# Bornes ajoutées et justifiées (non fournies par SCHEMA.md) :
# - une intervention de maintenance industrielle documentée dans ce corpus ne
#   dépasse pas 14 jours (20 160 minutes) d'indisponibilité continue ; au-delà,
#   la valeur ressemble à une valeur sentinelle (ex. 99999) plutôt qu'à une
#   mesure réelle et doit être examinée, pas acceptée telle quelle.
MAX_PLAUSIBLE_DOWNTIME_MINUTES = 20_160


def equipment_schema() -> pa.DataFrameSchema:
    """Retourne le DataFrameSchema Pandera de ``equipment.csv``."""
    return pa.DataFrameSchema(
        {
            "equipment_id": pa.Column(str, unique=True, nullable=False),
            "equipment_type": pa.Column(
                str, pa.Check.isin(sorted(EQUIPMENT_TYPES)), nullable=False
            ),
            "site_id": pa.Column(str, pa.Check.isin(sorted(SITE_IDS)), nullable=False),
            "commissioning_date": pa.Column(
                "datetime64[ns]",
                pa.Check(
                    lambda s: s <= pd.Timestamp.now(),
                    error="commissioning_date ne peut pas être dans le futur",
                ),
                nullable=False,
            ),
            "criticality": pa.Column(
                str, pa.Check.isin(sorted(CRITICALITIES)), nullable=False
            ),
            # nullable : SCHEMA.md documente manufacturer et rated_power_kw
            # comme "ou null" ; une valeur manquante n'est donc pas une
            # anomalie ici.
            "manufacturer": pa.Column(str, nullable=True),
            "rated_power_kw": pa.Column(
                float,
                pa.Check.gt(0, ignore_na=True, error="rated_power_kw doit être positif"),
                nullable=True,
            ),
        },
        strict=False,
        coerce=False,
    )


def events_schema() -> pa.DataFrameSchema:
    """Retourne le DataFrameSchema Pandera de ``events.csv``."""
    return pa.DataFrameSchema(
        {
            "event_id": pa.Column(str, unique=True, nullable=False),
            "equipment_id": pa.Column(str, nullable=False),
            "start_at": pa.Column("datetime64[ns, UTC]", nullable=False),
            # nullable : "fin, si applicable" (événement encore ouvert).
            "end_at": pa.Column("datetime64[ns, UTC]", nullable=True),
            "event_type": pa.Column(str, pa.Check.isin(sorted(EVENT_TYPES)), nullable=False),
            "severity": pa.Column(str, pa.Check.isin(sorted(SEVERITIES)), nullable=False),
            "period": pa.Column(str, nullable=False),
        },
        checks=[
            pa.Check(
                lambda df: df["end_at"].isna() | (df["end_at"] >= df["start_at"]),
                error="end_at doit être postérieur ou égal à start_at",
            )
        ],
        strict=False,
        coerce=False,
    )


def maintenance_schema() -> pa.DataFrameSchema:
    """Retourne le DataFrameSchema Pandera de ``maintenance_history.csv``."""
    return pa.DataFrameSchema(
        {
            "maintenance_id": pa.Column(str, unique=True, nullable=False),
            "event_id": pa.Column(str, nullable=False),
            "equipment_id": pa.Column(str, nullable=False),
            "opened_at": pa.Column("datetime64[ns, UTC]", nullable=False),
            # nullable : intervention encore ouverte.
            "closed_at": pa.Column("datetime64[ns, UTC]", nullable=True),
            "intervention_type": pa.Column(
                str, pa.Check.isin(sorted(INTERVENTION_TYPES)), nullable=False
            ),
            "outcome": pa.Column(str, pa.Check.isin(sorted(OUTCOMES)), nullable=False),
            "downtime_minutes": pa.Column(
                int,
                [
                    pa.Check.ge(0, error="downtime_minutes ne peut pas être négatif"),
                    pa.Check.le(
                        MAX_PLAUSIBLE_DOWNTIME_MINUTES,
                        error="downtime_minutes dépasse le seuil plausible (14 jours)",
                    ),
                ],
                nullable=False,
            ),
            "labor_hours": pa.Column(
                float, pa.Check.ge(0, ignore_na=True), nullable=True
            ),
            "parts_cost_eur": pa.Column(
                float, pa.Check.ge(0, ignore_na=True), nullable=True
            ),
            "parts_replaced_count": pa.Column(int, pa.Check.ge(0), nullable=False),
            "work_order_note": pa.Column(str, nullable=False),
            "period": pa.Column(str, nullable=False),
        },
        checks=[
            pa.Check(
                lambda df: df["closed_at"].isna() | (df["closed_at"] >= df["opened_at"]),
                error="closed_at doit être postérieur ou égal à opened_at",
            )
        ],
        strict=False,
        coerce=False,
    )
