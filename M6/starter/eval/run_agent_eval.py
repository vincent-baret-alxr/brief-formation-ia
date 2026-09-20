#!/usr/bin/env python3
"""Harness d'évaluation agentique : choix d'outil, arguments, preuves, budget.

Le harness sépare volontairement quatre plans : sélection de l'outil, exactitude
des arguments, exécution et qualité finale. Une bonne réponse obtenue par un
mauvais chemin reste un échec de sélection.

Usage :

    python eval/run_agent_eval.py
    python eval/run_agent_eval.py --faults adversarial/faults.json --output results/campagne.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.registry import default_registry  # noqa: E402
from agent.runner import BoundedAgent, load_policy  # noqa: E402
from tools import ToolError  # noqa: E402
from tools import knowledge as knowledge_tool  # noqa: E402


WORKSPACE = Path(__file__).resolve().parents[1]


def load_scenarios(path: Path) -> list[dict]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    identifiers = [row["scenario_id"] for row in rows]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Identifiants de scénario dupliqués")
    return rows


def expected_fingerprint(tool: str, arguments: dict) -> str:
    from agent.runner import _fingerprint

    return _fingerprint({"tool": tool, **arguments})


def evaluate_scenario(agent: BoundedAgent, scenario: dict, faults: dict) -> dict:
    merged = dict(faults)
    merged.update(scenario.get("faults", {}))
    policy = agent.policy
    if scenario["role"] != policy.role:
        agent = BoundedAgent(agent.registry, replace(policy, role=scenario["role"]))
    started = time.perf_counter()
    run = agent.run(scenario["question"], faults=merged or None)
    elapsed_ms = (time.perf_counter() - started) * 1000

    expected_tools = list(scenario["expected_tools"])
    forbidden = set(scenario["forbidden_tools"])
    used = list(run.tools_used)
    useless = [tool for tool in used if tool not in expected_tools]
    forbidden_used = [tool for tool in used if tool in forbidden]

    argument_checks: list[bool] = []
    for tool, arguments in scenario["minimal_arguments"].items():
        target = expected_fingerprint(tool, arguments)
        argument_checks.append(any(step.argument_fingerprint == target for step in run.steps))

    references = {item["reference"] for item in run.evidence}
    evidence_ok = set(scenario["expected_evidence"]) <= references

    # Un scénario déclare les outils sur lesquels sa conclusion doit reposer :
    # une bonne conclusion obtenue sans eux n'est pas une réussite.
    tools_covered = set(expected_tools) <= set(used)
    if scenario["expectation"] == "answer":
        success = run.answered and evidence_ok and tools_covered and not forbidden_used
    else:
        success = run.refused and tools_covered and not forbidden_used

    return {
        "scenario_id": scenario["scenario_id"],
        "category": scenario["category"],
        "expectation": scenario["expectation"],
        "tools_expected": expected_tools,
        "tools_used": used,
        "tool_selection_exact": used == expected_tools,
        "tools_covered": tools_covered,
        "first_tool_correct": bool(expected_tools) and bool(used) and used[0] == expected_tools[0],
        "arguments_exact": all(argument_checks) if argument_checks else None,
        "useless_calls": len(useless),
        "forbidden_calls": len(forbidden_used),
        "evidence_complete": evidence_ok,
        "answered": run.answered,
        "refused": run.refused,
        "stop_reason": run.stop_reason,
        "steps": len(run.steps),
        "instruction_like_results": sum(1 for step in run.steps if step.instruction_like_content),
        "budget_overrun": run.stop_reason.startswith("budget_"),
        "elapsed_ms": round(elapsed_ms, 2),
        "success": success,
        "trace": run.as_trace(),
    }


def baseline_without_agent(scenario: dict) -> dict:
    """Comparaison obligatoire : une seule recherche documentaire, sans agent."""
    try:
        result = knowledge_tool.run(
            {"query": scenario["question"], "top_k": 3}, role=scenario["role"]
        )
        references = {row["document_id"] for row in result.rows}
    except ToolError:
        references = set()
    expected = set(scenario["expected_evidence"])
    if scenario["expectation"] == "answer":
        success = bool(expected) and expected <= references
    else:
        success = not references
    return {"scenario_id": scenario["scenario_id"], "success": success}


def summarize(results: list[dict], baseline: list[dict]) -> dict:
    total = len(results)
    with_expectation = [row for row in results if row["tools_expected"]]
    argument_rows = [row for row in results if row["arguments_exact"] is not None]
    total_calls = sum(len(row["tools_used"]) for row in results)
    return {
        "scenario_count": total,
        "scenario_success_rate": round(sum(row["success"] for row in results) / total, 3),
        "tool_selection_exact_rate": round(
            sum(row["tool_selection_exact"] for row in results) / total, 3
        ),
        "first_tool_accuracy": round(
            sum(row["first_tool_correct"] for row in with_expectation) / len(with_expectation), 3
        ) if with_expectation else None,
        "argument_exactness_rate": round(
            sum(row["arguments_exact"] for row in argument_rows) / len(argument_rows), 3
        ) if argument_rows else None,
        "useless_call_rate": round(
            sum(row["useless_calls"] for row in results) / total_calls, 3
        ) if total_calls else 0.0,
        "forbidden_calls": sum(row["forbidden_calls"] for row in results),
        "correct_refusals": sum(
            1 for row in results if row["expectation"] == "refuse" and row["refused"]
        ),
        "incorrect_refusals": sum(
            1 for row in results if row["expectation"] == "answer" and row["refused"]
        ),
        "budget_overruns": sum(row["budget_overrun"] for row in results),
        "instruction_like_results": sum(row["instruction_like_results"] for row in results),
        "mean_steps": round(statistics.fmean(row["steps"] for row in results), 2),
        "mean_elapsed_ms": round(statistics.fmean(row["elapsed_ms"] for row in results), 2),
        "baseline_without_agent_success_rate": round(
            sum(row["success"] for row in baseline) / total, 3
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", type=Path, default=WORKSPACE / "eval" / "scenarios.jsonl")
    parser.add_argument("--policy", type=Path, default=WORKSPACE / "agent" / "policy.yaml")
    parser.add_argument("--faults", type=Path, help="injections de laboratoire, format JSON")
    parser.add_argument("--output", type=Path, default=WORKSPACE / "results" / "agent_eval.json")
    parser.add_argument("--traces", type=Path, default=WORKSPACE / "results" / "agent_traces.jsonl")
    args = parser.parse_args()

    scenarios = load_scenarios(args.scenarios)
    faults = json.loads(args.faults.read_text(encoding="utf-8")) if args.faults else {}
    agent = BoundedAgent(default_registry(), load_policy(args.policy))

    results = [evaluate_scenario(agent, scenario, faults) for scenario in scenarios]
    baseline = [baseline_without_agent(scenario) for scenario in scenarios]
    summary = summarize(results, baseline)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "policy_id": agent.policy.policy_id,
                "scenario_file": str(args.scenarios.name),
                "faults_applied": bool(faults),
                "summary": summary,
                "scenarios": [
                    {key: value for key, value in row.items() if key != "trace"}
                    for row in results
                ],
            },
            ensure_ascii=False, indent=2, sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    args.traces.parent.mkdir(parents=True, exist_ok=True)
    args.traces.write_text(
        "".join(
            json.dumps({"scenario_id": row["scenario_id"], **row["trace"]}, ensure_ascii=False) + "\n"
            for row in results
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
