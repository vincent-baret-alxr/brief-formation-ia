"""Chargement en lecture seule des sources M3.

Quatre sources sont ouvertes : les trois tables reçues en M2 et la table de
mesures ouverte en M3. L'état préparé de référence issu de M2 est chargé
séparément : c'est un point de départ possible, pas une source d'origine.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATA_DIR = REPOSITORY_ROOT / "data_pack" / "2026-S1"
REFERENCE_SUBPATH = Path("reference_runs") / "m2_for_m3"


def data_dir() -> Path:
    """Résout le dossier de données sans créer ni modifier de fichier."""
    return Path(os.environ.get("DIAGOPS_DATA_DIR", DEFAULT_DATA_DIR)).resolve()


def source_paths(root: Path | None = None) -> dict[str, Path]:
    """Retourne les chemins des quatre sources reçues."""
    base = (root or data_dir()).resolve()
    return {
        "equipment": base / "equipment" / "equipment.csv",
        "events": base / "events" / "events.csv",
        "maintenance": base / "maintenance" / "maintenance_history.csv",
        "sensors": base / "sensors" / "sensor_readings.csv",
    }


def reference_paths(root: Path | None = None) -> dict[str, Path]:
    """Retourne les chemins de l'état préparé de référence issu de M2."""
    base = (root or data_dir()).resolve() / REFERENCE_SUBPATH
    return {
        "equipment": base / "processed" / "equipment.csv",
        "events": base / "processed" / "events.csv",
        "maintenance": base / "processed" / "maintenance_history.csv",
        "quarantine": base / "quarantine" / "quarantine_m2.csv",
    }


def _load(paths: dict[str, Path], label: str) -> dict[str, pd.DataFrame]:
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"{label} absentes : " + ", ".join(missing))
    return {name: pd.read_csv(path) for name, path in paths.items()}


def load_sources(root: Path | None = None) -> dict[str, pd.DataFrame]:
    """Charge les CSV bruts sans transformation implicite.

    Les mesures sont lues telles quelles : `timestamp` reste une chaîne et
    `value` peut contenir des valeurs vides ou sentinelles. La normalisation
    est un choix du brief, pas un effet de bord du chargement.
    """
    return _load(source_paths(root), "Sources M3")


def load_reference(root: Path | None = None) -> dict[str, pd.DataFrame]:
    """Charge l'état préparé de référence M2 et sa quarantaine."""
    return _load(reference_paths(root), "Référence M2")


def file_sha256(path: Path) -> str:
    """Calcule le SHA-256 d'un fichier par blocs."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_checksums(root: Path | None = None) -> dict[str, str]:
    """Calcule les checksums des sources utilisées par le run."""
    return {name: file_sha256(path) for name, path in source_paths(root).items()}
