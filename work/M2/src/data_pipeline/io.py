"""Chargement en lecture seule des sources M2."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATA_DIR = REPOSITORY_ROOT / "data_pack" / "2026-S1"


def data_dir() -> Path:
    """Résout le dossier de données sans créer ni modifier de fichier."""
    return Path(os.environ.get("DIAGOPS_DATA_DIR", DEFAULT_DATA_DIR)).resolve()


def source_paths(root: Path | None = None) -> dict[str, Path]:
    """Retourne les chemins des trois tables tabulaires M2."""
    base = (root or data_dir()).resolve()
    return {
        "equipment": base / "equipment" / "equipment.csv",
        "events": base / "events" / "events.csv",
        "maintenance": base / "maintenance" / "maintenance_history.csv",
    }


def load_sources(root: Path | None = None) -> dict[str, pd.DataFrame]:
    """Charge les CSV bruts sans transformation implicite."""
    paths = source_paths(root)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Sources M2 absentes : " + ", ".join(missing))
    return {name: pd.read_csv(path) for name, path in paths.items()}


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
