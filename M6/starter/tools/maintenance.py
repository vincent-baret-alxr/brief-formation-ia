"""Outil `get_maintenance_history` : historique d'interventions, en lecture seule."""

from __future__ import annotations

from . import ToolResult, maintenance_table


SPEC = {
    "name": "get_maintenance_history",
    "purpose": "Lire les dernières interventions enregistrées pour un équipement.",
    "arguments": [
        {
            "name": "equipment_id",
            "type": "string",
            "required": True,
            "pattern": r"^EQ-[A-Z]+-\d+$",
            "description": "identifiant d'inventaire",
        },
        {
            "name": "limit",
            "type": "integer",
            "required": False,
            "minimum": 1,
            "maximum": 10,
            "default": 5,
            "description": "nombre d'interventions retournées, de la plus récente à la plus ancienne",
        },
    ],
    "result_fields": [
        "maintenance_id", "event_id", "opened_at", "closed_at",
        "intervention_type", "outcome", "downtime_minutes",
    ],
    "source_of_truth": "data_pack/2026-S1/maintenance/maintenance_history.csv",
    "authorized_roles": ["technicien", "superviseur", "auditeur"],
    "timeout_ms": 1200,
    "max_results": 10,
    "sensitive_data": "notes d'intervention internes ; aucune donnée personnelle attendue",
    "errors": ["identifiant inconnu", "table indisponible"],
    "degraded_mode": "résultat vide et motif ; une récidive ne se déduit pas d'un historique tronqué",
    "side_effects": False,
}


def run(arguments: dict, *, role: str) -> ToolResult:
    equipment_id = arguments["equipment_id"]
    limit = int(arguments.get("limit", 5))
    rows = [row for row in maintenance_table() if row["equipment_id"] == equipment_id]
    rows.sort(key=lambda row: row["opened_at"], reverse=True)
    selected = rows[:limit]
    return ToolResult(
        tool=SPEC["name"],
        rows=tuple({key: row[key] for key in SPEC["result_fields"]} for row in selected),
        source="maintenance_history.csv",
        truncated=len(rows) > len(selected),
        reason="" if selected else f"aucune intervention enregistrée pour {equipment_id}",
    )
