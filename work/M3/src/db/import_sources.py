"""Import des sources DiagOps en base.

L'import des équipements est fourni comme exemple : lecture, conversion,
insertion et comptage des lignes refusées. L'import des mesures est le travail
du brief : il doit être idempotent, et l'idempotence doit être démontrée, pas
affirmée.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Equipment


@dataclass
class ImportReport:
    """Comptages d'un import, à conserver comme preuve."""

    table: str
    read: int = 0
    inserted: int = 0
    rejected: int = 0
    reasons: dict[str, int] | None = None

    def as_dict(self) -> dict:
        return {
            "table": self.table,
            "read": self.read,
            "inserted": self.inserted,
            "rejected": self.rejected,
            "reasons": dict(sorted((self.reasons or {}).items())),
        }


def read_rows(path: Path) -> list[dict]:
    """Lit un CSV préparé sans conversion implicite."""
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def optional_date(value: str) -> date | None:
    """Convertit une date ISO, ou retourne None si la valeur est vide."""
    if not value:
        return None
    return date.fromisoformat(value)


def optional_float(value: str) -> float | None:
    """Convertit un nombre, ou retourne None si la valeur est vide."""
    if value in ("", None):
        return None
    return float(value)


def import_equipment(session: Session, path: Path) -> ImportReport:
    """Insère les équipements préparés et compte les lignes refusées.

    Chaque ligne est insérée dans son propre point de sauvegarde : une ligne
    refusée n'annule pas les précédentes et sa raison est conservée.
    """
    report = ImportReport(table="equipment", reasons={})
    for row in read_rows(path):
        report.read += 1
        try:
            with session.begin_nested():
                session.add(
                    Equipment(
                        equipment_id=row["equipment_id"],
                        equipment_type=row["equipment_type"],
                        site_id=row["site_id"],
                        commissioning_date=optional_date(row["commissioning_date"]),
                        criticality=row["criticality"],
                        manufacturer=row["manufacturer"] or None,
                        rated_power_kw=optional_float(row["rated_power_kw"]),
                    )
                )
            report.inserted += 1
        except IntegrityError as error:
            report.rejected += 1
            reason = type(error.orig).__name__ if error.orig else "IntegrityError"
            report.reasons[reason] = report.reasons.get(reason, 0) + 1
        except (KeyError, ValueError) as error:
            report.rejected += 1
            reason = type(error).__name__
            report.reasons[reason] = report.reasons.get(reason, 0) + 1
    return report


def import_measurements(session: Session, path: Path) -> ImportReport:
    """Insérer les mesures capteurs de manière idempotente.

    Contrat attendu :

    - deux exécutions successives laissent la table dans le même état ;
    - les mesures dont l'équipement est inconnu sont comptées, pas perdues ;
    - les horodatages illisibles sont comptés, pas convertis en silence ;
    - le rapport retourne les lignes lues, insérées et rejetées, avec les
      raisons de rejet.

    Plusieurs stratégies conviennent : contrôle préalable des clés existantes,
    contrainte d'unicité assortie d'une insertion tolérante, ou instruction
    d'insertion avec résolution de conflit. Le choix doit être justifié et son
    coût observé sur la volumétrie réelle du fichier.
    """
    raise NotImplementedError("À écrire pendant le brief online")
