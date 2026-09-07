"""Contrats M3.

Les domaines fermés et les identifiants de règles héritées sont fournis pour
éviter la ressaisie. Cette version choisit de repartir de la préparation de
référence M2 (`data_pack/2026-S1/reference_runs/m2_for_m3/`) plutôt que d'une
préparation personnelle : voir `docs/registre_regles.md` pour la
justification. Les schémas, plages physiques et rapprochements ci-dessous
sont donc écrits pour reproduire — puis étendre — le comportement documenté
dans `regles_m2.md`, et non pour réinventer des règles équivalentes.
"""

from __future__ import annotations

from datetime import date

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

# Nom de capteur attendu et unité annoncée par ce nom. Le fichier reçu ne
# garantit pas la cohérence entre les deux : c'est un contrôle à écrire.
SENSOR_UNITS = {
    "vibration_mm_s": "mm/s",
    "temperature_c": "°C",
    "pressure_bar": "bar",
    "current_a": "A",
    "rpm": "rpm",
}

# Facteurs de conversion vers l'unité canonique du capteur, observés dans le
# fichier reçu (température en kelvin, pression en kilopascal).
UNIT_CONVERSIONS = {
    "temperature_c": {"K": lambda kelvin: kelvin - 273.15},
    "pressure_bar": {"kPa": lambda kpa: kpa / 100.0},
}

MEASUREMENT_KEY = ("equipment_id", "timestamp", "sensor_name")

# Pas d'échantillonnage annoncé dans SCHEMA.md pour la livraison 2026-S1.
# Le pas réellement observé doit être mesuré, pas supposé.
ANNOUNCED_STEP_HOURS = 6
ANNOUNCED_PERIOD = "2026-S1"

# Bornes de la période annoncée : premier et dernier jour du semestre.
# "2026-S1" est traité comme un semestre (S1 = janvier-juin), cohérent avec
# les horodatages observés (janvier à juin 2026) et avec les 30 lignes
# `period=2026-S2` trouvées dans sensor_readings.csv.
PERIOD_BOUNDS = {"2026-S1": (date(2026, 1, 1), date(2026, 6, 30))}

# Domaines fermés hérités de M2 (mêmes valeurs que
# `data_pack/2026-S1/reference_runs/m2_for_m3/`), nécessaires pour rejouer
# R-EQ-002 et R-EQ-003.
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

# Borne ajoutée et justifiée (non fournie par SCHEMA.md ni par regles_m2.md) :
# au-delà de 14 jours (20 160 minutes) d'indisponibilité continue, une
# intervention de ce corpus ressemble à une valeur sentinelle plutôt qu'à une
# mesure réelle (cf. la valeur 99999 trouvée dans le fichier reçu). Reprend
# le seuil déjà retenu dans work/M2.
MAX_PLAUSIBLE_DOWNTIME_MINUTES = 20_160

# Règles de la préparation de référence M2, à reprendre avec un statut explicite.
# Source : data_pack/2026-S1/reference_runs/m2_for_m3/regles_m2.md
M2_RULE_IDS = (
    "R-EQ-001",
    "R-EQ-002",
    "R-EQ-003",
    "R-EQ-004",
    "R-EQ-005",
    "R-EQ-006",
    "R-EVT-001",
    "R-EVT-002",
    "R-EVT-003",
    "R-EVT-004",
    "R-EVT-005",
    "R-MNT-001",
    "R-MNT-002",
    "R-MNT-003",
    "R-MNT-004",
    "R-MNT-005",
    "R-MNT-006",
    "R-MNT-007",
    "R-MNT-008",
)


def sensor_value_ranges() -> dict[str, tuple[float, float]]:
    """Retourne les plages physiques plausibles par capteur.

    Bornes ajoutées et justifiées à partir de l'observation des séries reçues
    (percentiles, cf. `docs/diagnostic_multisource.md`) et de ce qui est
    physiquement plausible pour le type d'équipement instrumenté (parc
    industriel généraliste : pompes, compresseurs, fours, chillers...) :

    - ``current_a`` : un courant absorbé négatif n'existe pas ; 120 A couvre
      largement le maximum observé (34,1 A) avec une marge pour un
      équipement plus puissant non encore vu ;
    - ``vibration_mm_s`` : une amplitude de vibration est positive ; 45 mm/s
      correspond au seuil "dommage imminent" de la norme ISO 10816 pour les
      grandes machines, très au-dessus du maximum observé (9,76 mm/s) ;
    - ``temperature_c`` : -20°C (site non chauffé l'hiver) à 250°C (surface
      d'un équipement de type four ou unité vapeur) ; le maximum observé hors
      lignes mal étiquetées en kelvin est de 74,3°C ;
    - ``pressure_bar`` : une pression négative n'existe pas ; 25 bar couvre
      largement le maximum observé (8,1 bar après conversion des lignes en
      kPa) ;
    - ``rpm`` : une vitesse de rotation négative n'existe pas ; 3600 rpm est
      la vitesse de synchronisme d'un moteur asynchrone deux pôles à 50 Hz,
      au-dessus du maximum observé (1736,9 rpm).

    Ces bornes servent à isoler les valeurs impossibles (dont la valeur
    sentinelle ``-999`` observée sur les cinq capteurs), pas à qualifier une
    mesure de "normale" : une valeur dans la plage peut rester une anomalie
    métier (dérive, saut), à traiter séparément.
    """
    return {
        "current_a": (0.0, 120.0),
        "vibration_mm_s": (0.0, 45.0),
        "temperature_c": (-20.0, 250.0),
        "pressure_bar": (0.0, 25.0),
        "rpm": (0.0, 3600.0),
    }


def sensor_schema() -> pa.DataFrameSchema:
    """Retourne le schéma de validation de la table de mesures préparée.

    S'applique après normalisation du nom de capteur et de l'unité : les
    valeurs manquantes restent autorisées (``value`` nullable, cf. la mesure
    non relevée), la plage physique dépend du capteur et ne peut donc pas
    s'exprimer comme une borne de colonne indépendante.
    """
    ranges = sensor_value_ranges()

    def _within_physical_range(frame: pd.DataFrame) -> pd.Series:
        lower = frame["sensor_name"].map(lambda name: ranges.get(name, (float("-inf"), float("inf")))[0])
        upper = frame["sensor_name"].map(lambda name: ranges.get(name, (float("-inf"), float("inf")))[1])
        return frame["value"].isna() | frame["value"].between(lower, upper)

    return pa.DataFrameSchema(
        {
            "equipment_id": pa.Column(str, nullable=False),
            "timestamp": pa.Column("datetime64[ns, UTC]", nullable=False),
            "sensor_name": pa.Column(str, pa.Check.isin(sorted(SENSOR_UNITS)), nullable=False),
            "value": pa.Column(float, nullable=True),
            "unit": pa.Column(str, nullable=False),
            "period": pa.Column(str, nullable=False),
        },
        checks=[
            pa.Check(
                _within_physical_range,
                error="value hors plage physique plausible pour ce capteur",
            )
        ],
        strict=False,
        coerce=False,
    )


def align_measures_to_events(
    measures: pd.DataFrame,
    events: pd.DataFrame,
    before_hours: float,
    after_hours: float,
) -> pd.DataFrame:
    """Rapproche les mesures des événements par fenêtre temporelle.

    Fenêtre retenue et justification : 24 h avant le début de l'événement,
    6 h après — voir la question 8 de `docs/diagnostic_multisource.md`. Le
    rapprochement est un produit mesures × événements filtré par
    ``equipment_id`` puis par les bornes de fenêtre : une mesure peut
    apparaître pour plusieurs événements si leurs fenêtres se recouvrent, ce
    qui duplique la mesure de façon volontaire et contrôlée (colonne
    ``event_id`` distincte par ligne du résultat).
    """
    from src.data_pipeline.timeseries import to_utc, window_bounds

    windows = window_bounds(events, before_hours, after_hours)[
        ["event_id", "equipment_id", "window_start", "window_end"]
    ]

    working = measures.copy()
    working["_ts"] = to_utc(working["timestamp"])

    merged = working.merge(windows, on="equipment_id", suffixes=("", "_event"))
    within_window = (merged["_ts"] >= merged["window_start"]) & (
        merged["_ts"] <= merged["window_end"]
    )
    result = merged.loc[within_window].drop(columns=["_ts"]).reset_index(drop=True)
    result["before_hours"] = before_hours
    result["after_hours"] = after_hours
    return result
