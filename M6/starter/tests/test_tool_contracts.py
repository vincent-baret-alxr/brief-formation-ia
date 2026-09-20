"""Contrats d'outils : complétude, validation des arguments, bornes et rôles."""

from __future__ import annotations

import pytest

from agent.registry import ArgumentError, AuthorizationError, ToolSpec, UnknownTool, default_registry
from tools import diagnose, equipment, events, knowledge, maintenance


EXPECTED_TOOLS = (
    "diagnose_report", "get_equipment", "get_maintenance_history",
    "list_events", "search_knowledge",
)


@pytest.fixture(scope="module")
def registry():
    return default_registry()


def test_les_cinq_outils_sont_enregistres_et_geles(registry):
    assert registry.names() == EXPECTED_TOOLS
    assert registry.frozen


@pytest.mark.parametrize("module", [knowledge, equipment, events, maintenance, diagnose])
def test_chaque_contrat_est_complet(module):
    spec = ToolSpec.from_mapping(module.SPEC)
    assert spec.purpose and spec.source_of_truth and spec.degraded_mode
    assert spec.authorized_roles and spec.errors
    assert spec.timeout_ms > 0 and spec.max_results > 0
    assert spec.side_effects is False


def test_un_outil_a_effet_externe_est_refuse(registry):
    forbidden = dict(knowledge.SPEC, name="write_workorder", side_effects=True)
    with pytest.raises(ArgumentError):
        ToolSpec.from_mapping(forbidden)


def test_argument_inconnu_refuse(registry):
    with pytest.raises(ArgumentError):
        registry.validate("get_equipment", {"equipment_id": "EQ-PUMP-001", "site_id": "SITE-NORD"})


def test_argument_requis_absent_refuse(registry):
    with pytest.raises(ArgumentError):
        registry.validate("get_equipment", {})


def test_format_identifiant_invalide_refuse(registry):
    with pytest.raises(ArgumentError):
        registry.validate("get_equipment", {"equipment_id": "Pompe P-204"})


def test_enumeration_et_bornes_entieres(registry):
    with pytest.raises(ArgumentError):
        registry.validate("list_events", {"equipment_id": "EQ-PUMP-001", "severity": "urgent"})
    with pytest.raises(ArgumentError):
        registry.validate("list_events", {"equipment_id": "EQ-PUMP-001", "limit": 99})


def test_valeur_par_defaut_appliquee(registry):
    validated = registry.validate("list_events", {"equipment_id": "EQ-PUMP-001"})
    assert validated["limit"] == 5


def test_outil_inconnu_refuse(registry):
    with pytest.raises(UnknownTool):
        registry.spec("run_command")


def test_role_non_autorise_refuse(registry):
    with pytest.raises(AuthorizationError):
        registry.authorize("get_equipment", "public")


def test_limite_de_resultats_respectee(registry):
    result, _ = registry.call(
        "get_maintenance_history",
        {"equipment_id": "EQ-CONV-003", "limit": 10},
        role="technicien",
    )
    assert len(result.rows) <= registry.spec("get_maintenance_history").max_results


def test_champs_de_resultat_conformes_au_contrat(registry):
    result, _ = registry.call("get_equipment", {"equipment_id": "EQ-PUMP-001"}, role="technicien")
    assert set(result.rows[0]) == set(registry.spec("get_equipment").result_fields)


def test_filtrage_de_role_sur_le_corpus(registry):
    question = "Que prévoit la politique d'accès aux données pour les rôles autorisés ?"
    technicien, _ = registry.call("search_knowledge", {"query": question}, role="technicien")
    superviseur, _ = registry.call("search_knowledge", {"query": question}, role="superviseur")
    restreint = "DOC-DATA-ACCESS-001"
    assert restreint not in {row["document_id"] for row in technicien.rows}
    assert restreint in {row["document_id"] for row in superviseur.rows}


def test_revision_remplacee_jamais_servie(registry):
    result, _ = registry.call(
        "search_knowledge", {"query": "procédure de consignation électrique"}, role="technicien"
    )
    assert "DOC-LOTO-001" not in {row["document_id"] for row in result.rows}


def test_identifiant_inconnu_donne_un_resultat_vide_motive(registry):
    result, _ = registry.call("get_equipment", {"equipment_id": "EQ-PUMP-999"}, role="technicien")
    assert result.empty and result.reason


def test_rapport_inconnu_donne_un_resultat_vide_motive(registry):
    result, _ = registry.call("diagnose_report", {"report_id": "RPT-2027S1-9999"}, role="technicien")
    assert result.empty and result.reason


def test_lecture_de_rapport_exige_une_revue_humaine(registry):
    result, _ = registry.call("diagnose_report", {"report_id": "RPT-2027S1-0002"}, role="technicien")
    assert result.rows[0]["requires_human_review"] is True
