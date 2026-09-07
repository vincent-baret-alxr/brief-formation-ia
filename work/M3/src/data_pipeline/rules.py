"""Registre des règles de préparation.

Le registre rend visible ce qui vient de M2 et ce qui est ajouté en M3. Il ne
contient aucune règle métier : c'est un support de traçabilité, pas une
bibliothèque de contrôles.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

import pandas as pd


STATUSES = {"conservee", "modifiee", "etendue", "abandonnee", "nouvelle"}
INHERITED_STATUSES = {"conservee", "modifiee", "etendue", "abandonnee"}


@dataclass(frozen=True)
class Rule:
    """Une règle nommée, rattachée à une table et à un statut."""

    rule_id: str
    table: str
    status: str
    description: str
    origin: str = "M3"
    justification: str = ""

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(
                f"Statut inconnu pour {self.rule_id} : {self.status!r}. "
                f"Statuts admis : {sorted(STATUSES)}"
            )
        if self.origin == "M2" and self.status not in INHERITED_STATUSES:
            raise ValueError(
                f"Une règle héritée de M2 ne peut pas avoir le statut {self.status!r}"
            )
        if self.status in {"modifiee", "abandonnee"} and not self.justification:
            raise ValueError(
                f"La règle {self.rule_id} est {self.status} : une justification "
                "est obligatoire"
            )


@dataclass
class RuleRegistry:
    """Collection de règles, sans doublon d'identifiant."""

    rules: list[Rule] = field(default_factory=list)

    def add(self, rule: Rule) -> None:
        if any(existing.rule_id == rule.rule_id for existing in self.rules):
            raise ValueError(f"Règle déjà enregistrée : {rule.rule_id}")
        self.rules.append(rule)

    def extend(self, rules: Iterable[Rule]) -> None:
        for rule in rules:
            self.add(rule)

    def identifiers(self) -> set[str]:
        return {rule.rule_id for rule in self.rules}

    def missing(self, expected_ids: Iterable[str]) -> list[str]:
        """Règles attendues qui n'ont pas encore reçu de statut."""
        return sorted(set(expected_ids) - self.identifiers())

    def active(self) -> list[Rule]:
        """Règles qui doivent être appliquées par la pipeline."""
        return [rule for rule in self.rules if rule.status != "abandonnee"]

    def to_frame(self) -> pd.DataFrame:
        columns = ["rule_id", "origin", "table", "status", "description", "justification"]
        if not self.rules:
            return pd.DataFrame(columns=columns)
        frame = pd.DataFrame([vars(rule) for rule in self.rules])
        return frame.loc[:, columns].sort_values(["origin", "rule_id"], ignore_index=True)

    def to_markdown(self) -> str:
        frame = self.to_frame()
        header = "| Règle | Origine | Table | Statut | Contrôle | Justification |"
        separator = "|---|---|---|---|---|---|"
        lines = [header, separator]
        for row in frame.itertuples(index=False):
            lines.append(
                f"| `{row.rule_id}` | {row.origin} | {row.table} | {row.status} | "
                f"{row.description} | {row.justification} |"
            )
        return "\n".join(lines) + "\n"
