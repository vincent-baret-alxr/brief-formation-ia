"""Primitives locales de versionnement, promotion atomique et rollback."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


REQUIRED_RELEASE_FIELDS = {
    "release_id",
    "code_version",
    "model_version",
    "corpus_version",
    "index_version",
    "prompt_version",
    "evaluation_version",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Objet JSON attendu : {path}")
    return value


def validate_release(release: dict[str, Any]) -> None:
    missing = REQUIRED_RELEASE_FIELDS - set(release)
    if missing:
        raise ValueError(f"Champs de release absents : {sorted(missing)}")
    placeholders = [
        key for key in REQUIRED_RELEASE_FIELDS
        if not str(release[key]).strip() or str(release[key]).startswith("REPLACE_")
    ]
    if placeholders:
        raise ValueError(f"Valeurs de release non renseignées : {sorted(placeholders)}")


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def promote(candidate: Path, current: Path, history: Path) -> str:
    release = load_json(candidate)
    validate_release(release)
    history.mkdir(parents=True, exist_ok=True)
    if current.is_file():
        previous = load_json(current)
        validate_release(previous)
        archive = history / f"{previous['release_id']}.json"
        if not archive.exists():
            shutil.copy2(current, archive)
    atomic_write_json(current, release)
    return str(release["release_id"])


def rollback(current: Path, history: Path, release_id: str) -> str:
    target = history / f"{release_id}.json"
    release = load_json(target)
    validate_release(release)
    atomic_write_json(current, release)
    return str(release["release_id"])
