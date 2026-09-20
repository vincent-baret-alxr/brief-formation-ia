"""Bornes de la politique : budget, liste blanche, gel et non-élargissement."""

from __future__ import annotations

import dataclasses

import pytest
import yaml

from agent.registry import RegistryFrozen, ToolRegistry, default_registry
from agent.runner import BoundedAgent, load_policy
from tools import equipment as equipment_tool


POLICY_PATH = "agent/policy.yaml"


@pytest.fixture(scope="module")
def policy():
    return load_policy(POLICY_PATH)


def test_politique_immuable(policy):
    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.budget.max_steps = 99  # type: ignore[misc]
    with pytest.raises(AttributeError):
        policy.allowlist.add("write_workorder")  # type: ignore[attr-defined]


def test_politique_coherente_avec_le_registre(policy):
    assert policy.allowlist <= set(default_registry().names())
    assert policy.allow_dynamic_tools is False
    assert policy.budget.max_steps >= 1
    assert policy.budget.max_duration_ms > 0


def test_politique_autorisant_les_outils_dynamiques_refusee(tmp_path):
    raw = yaml.safe_load(open(POLICY_PATH, encoding="utf-8"))
    raw["execution"]["allow_dynamic_tools"] = True
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(ValueError):
        load_policy(path)


def test_budget_hors_plafond_refuse(tmp_path):
    raw = yaml.safe_load(open(POLICY_PATH, encoding="utf-8"))
    raw["budget"]["max_steps"] = 99
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(ValueError):
        load_policy(path)


def test_registre_gele_refuse_un_ajout():
    registry = default_registry()
    with pytest.raises(RegistryFrozen):
        registry.register(equipment_tool)


def test_liste_blanche_incoherente_refusee(policy):
    registry = ToolRegistry()
    registry.register(equipment_tool)
    registry.freeze()
    with pytest.raises(ValueError):
        BoundedAgent(registry, policy)


def test_outil_hors_liste_blanche_arrete_l_agent(policy):
    reduced = dataclasses.replace(policy, allowlist=frozenset({"get_equipment"}))
    agent = BoundedAgent(default_registry(), reduced)
    run = agent.run("Quelle procédure de consignation faut-il appliquer ?")
    assert run.refused
    assert run.stop_reason == "outil_hors_liste"
    assert not run.tools_used


def test_budget_d_etapes_applique(policy):
    class Bavard(BoundedAgent):
        def plan_next(self, question, state):
            return "list_events", {"equipment_id": "EQ-PUMP-001", "limit": len(state["tools_used"]) + 1}

    reduced = dataclasses.replace(
        policy, budget=dataclasses.replace(policy.budget, max_steps=2, max_tool_calls=2)
    )
    run = Bavard(default_registry(), reduced).run("Question sans fin")
    assert run.stop_reason == "budget_etapes_depasse"
    assert len(run.steps) == 2


def test_appel_repete_detecte(policy):
    class Repetiteur(BoundedAgent):
        def plan_next(self, question, state):
            return "get_equipment", {"equipment_id": "EQ-PUMP-001"}

    run = Repetiteur(default_registry(), policy).run("Question répétée")
    assert run.stop_reason == "appel_repete"
    assert len(run.steps) == 1


def test_erreur_outil_arrete_l_agent(policy):
    agent = BoundedAgent(default_registry(), policy)
    run = agent.run(
        "Quelle procédure de consignation faut-il appliquer ?",
        faults={"search_knowledge": {"error": "unavailable"}},
    )
    assert run.refused and run.stop_reason == "erreur_outil"


def test_absence_de_preuve_conduit_au_refus(policy):
    agent = BoundedAgent(default_registry(), policy)
    run = agent.run("Quel est le chiffre d'affaires du site SITE-NORD ?")
    assert run.refused and run.stop_reason == "preuve_insuffisante"
    assert not run.tools_used


def test_trace_sans_arguments_en_clair(policy):
    """Les étapes tracent des clés et une empreinte, jamais la valeur transmise.

    Les preuves, elles, restent citables : une référence d'enregistrement est
    nécessaire à l'audit et n'est pas un argument d'outil.
    """
    agent = BoundedAgent(default_registry(), policy)
    run = agent.run("Quelle est la criticité de EQ-PUMP-001 ?")
    trace = run.as_trace()
    assert "EQ-PUMP-001" not in str(trace["steps"])
    assert tuple(trace["steps"][0]["argument_keys"]) == ("equipment_id",)
    assert len(trace["steps"][0]["argument_fingerprint"]) == 12
    assert {"raw_arguments", "private_reasoning"}.isdisjoint(trace["steps"][0])
