"""Modèles DiagOps.

Un seul modèle est fourni comme exemple de déclaration : `Equipment`. Les autres
entités, leurs clés étrangères et la table des mesures sont à écrire pendant le
brief online, avec leurs types, leurs contraintes et leurs index justifiés.

Rappels de contrat, tirés de `data_pack/SCHEMA.md` :

- `events` : clé `event_id`, référence `equipment_id`, `start_at` obligatoire,
  `end_at` facultative, `severity` et `event_type` dans un domaine fermé ;
- `maintenance_history` : clé `maintenance_id`, références `event_id` et
  `equipment_id`, `closed_at`, `labor_hours` et `parts_cost_eur` facultatives ;
- `sensor_readings` : aucun identifiant de ligne. La clé logique est le triplet
  `equipment_id + timestamp + sensor_name`, à exprimer par une contrainte
  d'unicité. La référence vers `equipment` doit être déclarée et le sort des
  mesures orphelines décidé.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base déclarative commune à tous les modèles DiagOps."""


class Equipment(Base):
    """Inventaire des équipements suivis.

    Exemple complet de déclaration : clé primaire explicite, colonnes
    obligatoires, colonnes facultatives et longueurs bornées. Les types retenus
    ici sont un point de départ discutable, pas une norme.
    """

    __tablename__ = "equipment"

    equipment_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    equipment_type: Mapped[str] = mapped_column(String(64), nullable=False)
    site_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    commissioning_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    criticality: Mapped[str] = mapped_column(String(16), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rated_power_kw: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - confort de lecture
        return f"<Equipment {self.equipment_id} {self.equipment_type}>"


# À écrire pendant le brief online :
#
# class Event(Base): ...
# class Maintenance(Base): ...
# class SensorReading(Base): ...
#
# `SensorReading` n'est pas créée par la première migration : elle fait l'objet
# d'une seconde migration, appliquée sur une base déjà chargée.
