"""Outil `diagnose_report` : lecture structurée d'un rapport technicien.

L'outil lit un rapport et en extrait le squelette du contrat DiagOps. Il
n'appelle aucun modèle, ne déclenche aucune intervention et n'écrit rien. Sa
sortie est une lecture, pas un diagnostic validé : `requires_human_review` reste
vrai et la confiance n'est pas renseignée.
"""

from __future__ import annotations

import re

from . import ToolResult, events_table, reports_table


SYMPTOM_TERMS = {
    "vibration": "vibration anormale",
    "bruit": "bruit anormal",
    "temperature": "température hors consigne",
    "givre": "givre ou échange thermique dégradé",
    "pression": "pression hors consigne",
    "courant": "courant moteur anormal",
    "variateur": "défaut de variateur",
    "fuite": "fuite constatée",
    "arret": "arrêts intempestifs",
    "defaut": "défaut signalé sans qualification",
}

SPEC = {
    "name": "diagnose_report",
    "purpose": "Lire un rapport technicien et en extraire le squelette du contrat DiagOps.",
    "arguments": [
        {
            "name": "report_id",
            "type": "string",
            "required": True,
            "pattern": r"^RPT-\d{4}S\d-\d{4}$",
            "description": "identifiant de rapport technicien",
        },
    ],
    "result_fields": [
        "report_id", "equipment_id", "symptom", "severity_hint",
        "evidence", "requires_human_review",
    ],
    "source_of_truth": "data_pack/*/reports/reports.jsonl et events.csv pour la sévérité liée",
    "authorized_roles": ["technicien", "superviseur", "auditeur"],
    "timeout_ms": 1000,
    "max_results": 1,
    "sensitive_data": "texte libre pouvant citer une personne ; seul le symptôme extrait est rendu",
    "errors": ["rapport inconnu", "source indisponible"],
    "degraded_mode": "résultat vide et motif ; aucune hypothèse n'est produite sans rapport",
    "side_effects": False,
}

NORMALIZE = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")


def _symptoms(note: str) -> list[str]:
    lowered = note.lower().translate(NORMALIZE)
    found = [label for term, label in SYMPTOM_TERMS.items() if re.search(term, lowered)]
    return found or ["symptôme non qualifié par le rapport"]


def _severity_hint(event_id: str | None) -> str:
    if not event_id:
        return "unknown"
    for row in events_table():
        if row["event_id"] == event_id:
            return row["severity"]
    return "unknown"


def run(arguments: dict, *, role: str) -> ToolResult:
    report_id = arguments["report_id"]
    report = reports_table().get(report_id)
    if report is None:
        return ToolResult(
            tool=SPEC["name"],
            source="reports.jsonl",
            reason=f"rapport inconnu : {report_id}",
        )
    evidence = [report_id]
    if report.get("event_id"):
        evidence.append(report["event_id"])
    row = {
        "report_id": report_id,
        "equipment_id": report.get("equipment_id"),
        "symptom": "; ".join(_symptoms(report["technician_note"])),
        "severity_hint": _severity_hint(report.get("event_id")),
        "evidence": evidence,
        "requires_human_review": True,
    }
    return ToolResult(tool=SPEC["name"], rows=(row,), source="reports.jsonl")
