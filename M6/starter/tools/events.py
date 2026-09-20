"""Outil `list_events` : événements d'un équipement, en lecture seule."""

from __future__ import annotations

from . import ToolResult, events_table


SEVERITIES = ["low", "medium", "high", "critical"]

SPEC = {
    "name": "list_events",
    "purpose": "Lister les événements récents rattachés à un équipement identifié.",
    "arguments": [
        {
            "name": "equipment_id",
            "type": "string",
            "required": True,
            "pattern": r"^EQ-[A-Z]+-\d+$",
            "description": "identifiant d'inventaire",
        },
        {
            "name": "severity",
            "type": "enum",
            "required": False,
            "values": SEVERITIES,
            "description": "filtre de sévérité ; absent, toutes les sévérités sont rendues",
        },
        {
            "name": "limit",
            "type": "integer",
            "required": False,
            "minimum": 1,
            "maximum": 10,
            "default": 5,
            "description": "nombre d'événements retournés, du plus récent au plus ancien",
        },
    ],
    "result_fields": ["event_id", "equipment_id", "start_at", "end_at", "event_type", "severity"],
    "source_of_truth": "data_pack/2026-S1/events/events.csv",
    "authorized_roles": ["technicien", "superviseur", "auditeur"],
    "timeout_ms": 1000,
    "max_results": 10,
    "sensitive_data": "aucune donnée personnelle",
    "errors": ["identifiant inconnu", "sévérité hors énumération", "table indisponible"],
    "degraded_mode": "résultat vide et motif ; l'absence d'événement n'est pas une preuve d'absence de défaut",
    "side_effects": False,
}


def run(arguments: dict, *, role: str) -> ToolResult:
    equipment_id = arguments["equipment_id"]
    severity = arguments.get("severity")
    limit = int(arguments.get("limit", 5))
    rows = [
        row for row in events_table()
        if row["equipment_id"] == equipment_id
        and (severity is None or row["severity"] == severity)
    ]
    rows.sort(key=lambda row: row["start_at"], reverse=True)
    selected = rows[:limit]
    return ToolResult(
        tool=SPEC["name"],
        rows=tuple({key: row[key] for key in SPEC["result_fields"]} for row in selected),
        source="events.csv",
        truncated=len(rows) > len(selected),
        reason="" if selected else f"aucun événement pour {equipment_id} avec ce filtre",
    )
