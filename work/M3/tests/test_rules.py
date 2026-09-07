import pytest

from contracts.schemas import M2_RULE_IDS
from src.data_pipeline.rules import Rule, RuleRegistry


def inherited(rule_id: str, status: str = "conservee", justification: str = "") -> Rule:
    return Rule(
        rule_id=rule_id,
        table="equipment",
        status=status,
        description="contrôle hérité",
        origin="M2",
        justification=justification,
    )


def test_rule_rejects_unknown_status():
    with pytest.raises(ValueError):
        Rule(rule_id="SEN-GAP-001", table="sensors", status="peut_etre", description="")


def test_inherited_rule_cannot_be_declared_new():
    with pytest.raises(ValueError):
        inherited("R-EQ-001", status="nouvelle")


def test_abandoned_rule_requires_a_justification():
    with pytest.raises(ValueError):
        inherited("R-EQ-004", status="abandonnee")
    assert inherited("R-EQ-004", status="abandonnee", justification="remplacée").status == (
        "abandonnee"
    )


def test_registry_refuses_a_duplicated_identifier():
    registry = RuleRegistry()
    registry.add(inherited("R-EQ-001"))
    with pytest.raises(ValueError):
        registry.add(inherited("R-EQ-001"))


def test_registry_lists_the_m2_rules_still_without_status():
    registry = RuleRegistry()
    registry.add(inherited("R-EQ-001"))
    missing = registry.missing(M2_RULE_IDS)
    assert "R-EQ-001" not in missing
    assert len(missing) == len(M2_RULE_IDS) - 1


def test_active_rules_exclude_abandoned_ones():
    registry = RuleRegistry()
    registry.extend(
        [
            inherited("R-EQ-001"),
            inherited("R-EQ-004", status="abandonnee", justification="remplacée"),
            Rule(
                rule_id="SEN-KEY-001",
                table="sensors",
                status="nouvelle",
                description="unicité de la clé logique",
            ),
        ]
    )
    assert {rule.rule_id for rule in registry.active()} == {"R-EQ-001", "SEN-KEY-001"}
    assert list(registry.to_frame().columns)[:4] == ["rule_id", "origin", "table", "status"]
