"""Outil `get_equipment` : fiche d'un équipement, en lecture seule."""

from __future__ import annotations

from . import ToolResult, equipment_table


SPEC = {
    "name": "get_equipment",
    "purpose": "Lire la fiche d'inventaire d'un équipement identifié.",
    "arguments": [
        {
            "name": "equipment_id",
            "type": "string",
            "required": True,
            "pattern": r"^EQ-[A-Z]+-\d+$",
            "description": "identifiant d'inventaire, jamais un nom d'usage",
        },
    ],
    "result_fields": [
        "equipment_id", "equipment_type", "site_id", "criticality",
        "commissioning_date", "manufacturer", "rated_power_kw",
    ],
    "source_of_truth": "data_pack/2026-S1/equipment/equipment.csv",
    "authorized_roles": ["technicien", "superviseur", "auditeur"],
    "timeout_ms": 800,
    "max_results": 1,
    "sensitive_data": "aucune donnée personnelle ; site et criticité restent internes",
    "errors": ["identifiant inconnu", "table indisponible"],
    "degraded_mode": "résultat vide et motif ; l'agent ne devine pas l'équipement",
    "side_effects": False,
}


def run(arguments: dict, *, role: str) -> ToolResult:
    equipment_id = arguments["equipment_id"]
    row = equipment_table().get(equipment_id)
    if row is None:
        return ToolResult(
            tool=SPEC["name"],
            source="equipment.csv",
            reason=f"identifiant inconnu : {equipment_id}",
        )
    return ToolResult(
        tool=SPEC["name"],
        rows=({key: row[key] for key in SPEC["result_fields"]},),
        source="equipment.csv",
    )
