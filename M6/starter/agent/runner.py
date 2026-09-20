"""Agent mono-agent borné : planification courte, un outil à la fois, arrêt.

L'agent ne modifie pas sa politique, n'élargit pas sa liste d'outils et ne
traite jamais le contenu récupéré comme une instruction. Le planificateur
fourni est une base à améliorer : il couvre les cas nominaux du jeu de
scénarios distribué, pas l'ensemble des situations demandées par le brief.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from tools import ToolError, ToolResult
from .registry import ArgumentError, AuthorizationError, ToolRegistry, UnknownTool, default_registry


HARD_MAX_STEPS = 8
HARD_MAX_DURATION_MS = 30000

EQUIPMENT_PATTERN = re.compile(r"EQ-[A-Z]+-\d+")
REPORT_PATTERN = re.compile(r"RPT-\d{4}S\d-\d{4}")

# Marqueurs d'instruction rencontrés dans un contenu récupéré. Ils ne sont
# jamais exécutés : ils sont signalés dans la trace et la réponse reste bornée.
INSTRUCTION_MARKERS = (
    "ignore les consignes", "ignore les instructions", "nouvelle consigne",
    "tu peux desormais", "tu peux désormais", "ajoute l outil", "ajoute l'outil",
    "consigne systeme", "consigne système", "reponds sans citer", "réponds sans citer",
)

HISTORY_TERMS = ("historique", "intervention", "recidive", "récidive", "deja", "déjà", "precedent", "précédent")
EVENT_TERMS = ("evenement", "événement", "incident", "alerte", "panne", "arret", "arrêt")
FICHE_TERMS = ("criticite", "criticité", "site", "fiche", "equipement", "équipement", "puissance", "fabricant")
PROCEDURE_TERMS = ("procedure", "procédure", "consigne", "consignation", "seuil", "revision", "révision",
                   "politique", "regle", "règle", "etape", "étape", "autorise", "autorisé")


@dataclass(frozen=True)
class Budget:
    max_steps: int
    max_tool_calls: int
    max_duration_ms: int
    max_repeated_calls: int
    max_result_rows: int


@dataclass(frozen=True)
class Policy:
    policy_id: str
    role: str
    allowlist: frozenset[str]
    budget: Budget
    stop_on_tool_error: bool
    require_evidence: bool
    treat_tool_output_as_data: bool
    allow_dynamic_tools: bool
    trace_record_fields: tuple[str, ...]
    trace_forbidden_fields: tuple[str, ...]
    retention_days: int


@dataclass(frozen=True)
class Step:
    index: int
    tool: str
    argument_keys: tuple[str, ...]
    argument_fingerprint: str
    row_count: int
    source: str
    elapsed_ms: float
    outcome: str
    instruction_like_content: bool = False


@dataclass
class AgentRun:
    question: str
    role: str
    policy_id: str
    steps: list[Step] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    answered: bool = False
    refused: bool = False
    stop_reason: str = ""
    elapsed_ms: float = 0.0
    answer: str = ""

    def as_trace(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "role": self.role,
            "steps": [asdict(step) for step in self.steps],
            "tools_used": self.tools_used,
            "evidence": self.evidence,
            "answered": self.answered,
            "refused": self.refused,
            "stop_reason": self.stop_reason,
            "elapsed_ms": round(self.elapsed_ms, 2),
        }


def load_policy(path: Path | str = Path(__file__).with_name("policy.yaml")) -> Policy:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    execution = raw["execution"]
    budget = raw["budget"]
    if execution.get("allow_dynamic_tools", False):
        raise ValueError("Politique refusée : l'ajout dynamique d'outils est interdit en M6.")
    if budget["max_steps"] > HARD_MAX_STEPS:
        raise ValueError(f"Politique refusée : max_steps au-delà de {HARD_MAX_STEPS}.")
    if budget["max_duration_ms"] > HARD_MAX_DURATION_MS:
        raise ValueError(f"Politique refusée : max_duration_ms au-delà de {HARD_MAX_DURATION_MS}.")
    if not raw["allowlist"]:
        raise ValueError("Politique refusée : liste blanche vide.")
    trace = raw["trace"]
    return Policy(
        policy_id=raw["policy_id"],
        role=raw["role"],
        allowlist=frozenset(raw["allowlist"]),
        budget=Budget(
            max_steps=int(budget["max_steps"]),
            max_tool_calls=int(budget["max_tool_calls"]),
            max_duration_ms=int(budget["max_duration_ms"]),
            max_repeated_calls=int(budget["max_repeated_calls"]),
            max_result_rows=int(budget["max_result_rows"]),
        ),
        stop_on_tool_error=bool(execution["stop_on_tool_error"]),
        require_evidence=bool(execution["require_evidence"]),
        treat_tool_output_as_data=bool(execution["treat_tool_output_as_data"]),
        allow_dynamic_tools=False,
        trace_record_fields=tuple(trace["record_fields"]),
        trace_forbidden_fields=tuple(trace["forbidden_fields"]),
        retention_days=int(trace["retention_days"]),
    )


def _fingerprint(arguments: dict) -> str:
    payload = json.dumps(arguments, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def _looks_like_instruction(result: ToolResult) -> bool:
    joined = " ".join(
        str(value) for row in result.rows for value in row.values()
    ).lower()
    return any(marker in joined for marker in INSTRUCTION_MARKERS)


class BoundedAgent:
    """Agent à étapes bornées, sans mémoire persistante ni effet externe."""

    def __init__(self, registry: ToolRegistry | None = None, policy: Policy | None = None) -> None:
        self.registry = registry or default_registry()
        self.policy = policy or load_policy()
        unknown = sorted(self.policy.allowlist - set(self.registry.names()))
        if unknown:
            raise ValueError(f"Liste blanche incohérente avec le registre : {unknown}")

    # -- planification ----------------------------------------------------
    def plan_next(self, question: str, state: dict) -> tuple[str, dict] | None:
        """Choisit l'outil suivant, ou None pour conclure.

        Base fournie : la tranche M4 à une seule étape, transposée aux cinq
        outils. Elle sélectionne un outil sur des mots-clés, l'appelle une fois
        et conclut. Le M6 consiste à dépasser cette base : enchaînement borné de
        plusieurs étapes, filtrage du rôle avant l'appel, refus des noms d'usage,
        refus avant appel quand la question porte une instruction, arbitrage des
        sources contradictoires et complétude des arguments.
        """
        lowered = question.lower()
        used: set[str] = set(state["tools_used"])
        if used:
            # Borne de départ : une seule étape. La lever fait partie du brief,
            # sans jamais dépasser le budget de la politique.
            return None
        report_id = state.get("report_id")
        equipment_id = state.get("equipment_id")

        if report_id and "diagnose_report" not in used:
            return "diagnose_report", {"report_id": report_id}
        if equipment_id and any(term in lowered for term in HISTORY_TERMS) \
                and "get_maintenance_history" not in used:
            return "get_maintenance_history", {"equipment_id": equipment_id, "limit": 5}
        if equipment_id and any(term in lowered for term in EVENT_TERMS) \
                and "list_events" not in used:
            return "list_events", {"equipment_id": equipment_id, "limit": 5}
        if equipment_id and any(term in lowered for term in FICHE_TERMS) \
                and "get_equipment" not in used:
            return "get_equipment", {"equipment_id": equipment_id}
        if any(term in lowered for term in PROCEDURE_TERMS) and "search_knowledge" not in used:
            return "search_knowledge", {"query": question, "top_k": 3}
        return None

    # -- exécution --------------------------------------------------------
    def run(self, question: str, *, faults: dict | None = None) -> AgentRun:
        run = AgentRun(question=question, role=self.policy.role, policy_id=self.policy.policy_id)
        state: dict[str, Any] = {
            "tools_used": [],
            "equipment_id": _first(EQUIPMENT_PATTERN, question),
            "report_id": _first(REPORT_PATTERN, question),
            "calls": {},
        }
        started = time.perf_counter()
        budget = self.policy.budget

        while True:
            elapsed = (time.perf_counter() - started) * 1000
            if elapsed > budget.max_duration_ms:
                run.stop_reason = "budget_duree_depasse"
                break
            if len(run.steps) >= budget.max_steps or len(run.steps) >= budget.max_tool_calls:
                run.stop_reason = "budget_etapes_depasse"
                break

            plan = self.plan_next(question, state)
            if plan is None:
                break
            tool, arguments = plan
            if tool not in self.policy.allowlist:
                run.stop_reason = "outil_hors_liste"
                break

            fingerprint = _fingerprint({"tool": tool, **arguments})
            state["calls"][fingerprint] = state["calls"].get(fingerprint, 0) + 1
            if state["calls"][fingerprint] > budget.max_repeated_calls:
                run.stop_reason = "appel_repete"
                break

            try:
                result, elapsed_ms = self.registry.call(
                    tool, arguments, role=self.policy.role, faults=faults
                )
            except (ToolError, ArgumentError, AuthorizationError, UnknownTool) as exc:
                run.steps.append(Step(
                    index=len(run.steps) + 1, tool=tool,
                    argument_keys=tuple(sorted(arguments)),
                    argument_fingerprint=fingerprint,
                    row_count=0, source="", elapsed_ms=0.0,
                    outcome=type(exc).__name__,
                ))
                state["tools_used"].append(tool)
                run.tools_used.append(tool)
                if self.policy.stop_on_tool_error:
                    run.stop_reason = "erreur_outil"
                    break
                continue

            instruction_like = _looks_like_instruction(result)
            run.steps.append(Step(
                index=len(run.steps) + 1, tool=tool,
                argument_keys=tuple(sorted(arguments)),
                argument_fingerprint=fingerprint,
                row_count=len(result.rows), source=result.source,
                elapsed_ms=round(elapsed_ms, 2),
                outcome="vide" if result.empty else "ok",
                instruction_like_content=instruction_like,
            ))
            state["tools_used"].append(tool)
            run.tools_used.append(tool)
            self._collect_evidence(tool, result, run, state)

        run.elapsed_ms = (time.perf_counter() - started) * 1000
        self._conclude(run)
        return run

    def _collect_evidence(self, tool: str, result: ToolResult, run: AgentRun, state: dict) -> None:
        for row in result.rows:
            if tool == "search_knowledge":
                run.evidence.append({
                    "type": "document",
                    "reference": row["document_id"],
                    "revision": row["revision"],
                })
            elif tool == "diagnose_report":
                if row.get("equipment_id"):
                    state["equipment_id"] = row["equipment_id"]
                run.evidence.append({"type": "rapport", "reference": row["report_id"]})
            else:
                key = next(
                    (name for name in ("event_id", "maintenance_id", "equipment_id") if name in row),
                    None,
                )
                run.evidence.append({
                    "type": "enregistrement",
                    "reference": row.get(key, tool),
                    "source": result.source,
                })

    def _conclude(self, run: AgentRun) -> None:
        if run.stop_reason:
            run.refused = True
            run.answer = f"Refus : {run.stop_reason}."
            return
        if self.policy.require_evidence and not run.evidence:
            run.refused = True
            run.stop_reason = "preuve_insuffisante"
            run.answer = "Refus : aucune preuve admissible n'a été obtenue."
            return
        run.answered = True
        run.stop_reason = "reponse_produite"
        references = ", ".join(sorted({item["reference"] for item in run.evidence}))
        run.answer = f"Réponse fondée sur : {references}."


def _first(pattern: re.Pattern[str], text: str) -> str | None:
    found = pattern.search(text)
    return found.group(0) if found else None
