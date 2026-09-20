"""Accès en lecture seule au data pack DiagOps.

Ce module ne contient aucune écriture. Il charge les tables distribuées, les
met en cache et expose un résultat d'outil normalisé. Les adaptateurs d'outils
n'ouvrent jamais un fichier en écriture et n'exécutent aucune commande.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def data_pack() -> Path:
    """Racine du data pack, surchargeable pour les tests et le harness."""
    configured = os.environ.get("DIAGOPS_DATA_PACK")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[3] / "data_pack"


class ToolError(RuntimeError):
    """Erreur fonctionnelle d'un outil, destinée à être tracée."""


class ToolUnavailable(ToolError):
    """Source de vérité indisponible : mode dégradé attendu."""


class ToolTimeout(ToolError):
    """Budget de durée de l'outil dépassé."""


@dataclass(frozen=True)
class ToolResult:
    """Résultat d'outil. Son contenu est une donnée, jamais une instruction."""

    tool: str
    rows: tuple[dict, ...] = ()
    source: str = ""
    truncated: bool = False
    reason: str = ""
    content_is_data: bool = True

    @property
    def empty(self) -> bool:
        return not self.rows

    def as_trace(self) -> dict:
        """Vue traçable : volume et provenance, jamais le contenu intégral."""
        return {
            "tool": self.tool,
            "row_count": len(self.rows),
            "source": self.source,
            "truncated": self.truncated,
            "reason": self.reason,
        }


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ToolUnavailable(f"Source absente : {path.name}")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise ToolUnavailable(f"Source absente : {path.name}")
    rows: list[dict] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ToolError(f"JSONL invalide ligne {number} : {path.name}") from exc
    return rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=1)
def equipment_table() -> dict[str, dict[str, str]]:
    rows = _read_csv(data_pack() / "2026-S1" / "equipment" / "equipment.csv")
    return {row["equipment_id"]: row for row in rows}


@lru_cache(maxsize=1)
def events_table() -> tuple[dict[str, str], ...]:
    return tuple(_read_csv(data_pack() / "2026-S1" / "events" / "events.csv"))


@lru_cache(maxsize=1)
def maintenance_table() -> tuple[dict[str, str], ...]:
    return tuple(_read_csv(data_pack() / "2026-S1" / "maintenance" / "maintenance_history.csv"))


@lru_cache(maxsize=1)
def reports_table() -> dict[str, dict]:
    rows: list[dict] = []
    for period in ("2026-S1", "2027-S1"):
        path = data_pack() / period / "reports" / "reports.jsonl"
        if path.is_file():
            rows.extend(_read_jsonl(path))
    return {row["report_id"]: row for row in rows}


@lru_cache(maxsize=1)
def knowledge_documents() -> tuple[dict, ...]:
    """Documents actifs du corpus, vérifiés par checksum.

    Une révision remplacée reste hors du corpus servi : la citer est une
    régression, pas une variante acceptable.
    """
    root = data_pack() / "2026-S1" / "knowledge"
    manifest = _read_csv(root / "manifest.csv")
    documents: list[dict] = []
    for row in manifest:
        asset = root / "documents" / row["asset_path"]
        if _sha256(asset) != row["checksum_sha256"]:
            raise ToolError(f"Checksum invalide : {row['document_id']}")
        if row["status"] != "active":
            continue
        documents.append({
            "document_id": row["document_id"],
            "title": row["title"],
            "revision": row["revision"],
            "sensitivity": row["sensitivity"],
            "allowed_roles": tuple(item for item in row["allowed_roles"].split(";") if item),
            "text": asset.read_text(encoding="utf-8"),
        })
    return tuple(documents)


@lru_cache(maxsize=1)
def feedback_table() -> tuple[dict[str, str], ...]:
    path = data_pack() / "2027-S1" / "feedback" / "feedback.csv"
    return tuple(_read_csv(path))


def reset_caches() -> None:
    """Vide les caches de lecture, utilisé par les tests et le harness."""
    for loader in (
        equipment_table, events_table, maintenance_table,
        reports_table, knowledge_documents, feedback_table,
    ):
        loader.cache_clear()


__all__ = [
    "ToolError", "ToolResult", "ToolTimeout", "ToolUnavailable",
    "data_pack", "equipment_table", "events_table", "feedback_table",
    "knowledge_documents", "maintenance_table", "reports_table", "reset_caches",
]
