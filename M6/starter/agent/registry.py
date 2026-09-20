"""Registre d'outils : contrats, autorisation, bornes et gel.

Le registre est la seule porte d'entrée vers un outil. Il valide les arguments
avant exécution, refuse un outil hors liste, applique la limite de résultats et
la durée maximale déclarées, puis se gèle. Aucun outil ne peut être ajouté après
le gel : l'agent ne peut pas élargir ses capacités en cours d'exécution.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from types import ModuleType
from typing import Callable

from tools import ToolResult, ToolTimeout, ToolUnavailable


class RegistryFrozen(RuntimeError):
    """Tentative d'enregistrement après le gel du registre."""


class UnknownTool(KeyError):
    """Outil absent du registre ou hors liste blanche."""


class ArgumentError(ValueError):
    """Argument manquant, inconnu ou non conforme au contrat."""


class AuthorizationError(PermissionError):
    """Rôle non autorisé pour cet outil."""


@dataclass(frozen=True)
class ArgumentSpec:
    name: str
    type: str
    required: bool = False
    description: str = ""
    pattern: str | None = None
    values: tuple[str, ...] = ()
    minimum: int | None = None
    maximum: int | None = None
    min_length: int | None = None
    max_length: int | None = None
    default: object = None


@dataclass(frozen=True)
class ToolSpec:
    name: str
    purpose: str
    arguments: tuple[ArgumentSpec, ...]
    result_fields: tuple[str, ...]
    source_of_truth: str
    authorized_roles: tuple[str, ...]
    timeout_ms: int
    max_results: int
    sensitive_data: str
    errors: tuple[str, ...]
    degraded_mode: str
    side_effects: bool = False

    @classmethod
    def from_mapping(cls, mapping: dict) -> "ToolSpec":
        required = {
            "name", "purpose", "arguments", "result_fields", "source_of_truth",
            "authorized_roles", "timeout_ms", "max_results", "sensitive_data",
            "errors", "degraded_mode",
        }
        missing = required - set(mapping)
        if missing:
            raise ArgumentError(f"Contrat d'outil incomplet : {sorted(missing)}")
        if mapping.get("side_effects", False):
            raise ArgumentError(f"Outil à effet externe refusé : {mapping['name']}")
        arguments = tuple(
            ArgumentSpec(
                name=item["name"],
                type=item["type"],
                required=item.get("required", False),
                description=item.get("description", ""),
                pattern=item.get("pattern"),
                values=tuple(item.get("values", ())),
                minimum=item.get("minimum"),
                maximum=item.get("maximum"),
                min_length=item.get("min_length"),
                max_length=item.get("max_length"),
                default=item.get("default"),
            )
            for item in mapping["arguments"]
        )
        return cls(
            name=mapping["name"],
            purpose=mapping["purpose"],
            arguments=arguments,
            result_fields=tuple(mapping["result_fields"]),
            source_of_truth=mapping["source_of_truth"],
            authorized_roles=tuple(mapping["authorized_roles"]),
            timeout_ms=int(mapping["timeout_ms"]),
            max_results=int(mapping["max_results"]),
            sensitive_data=mapping["sensitive_data"],
            errors=tuple(mapping["errors"]),
            degraded_mode=mapping["degraded_mode"],
            side_effects=False,
        )


class ToolRegistry:
    """Registre gelable d'outils en lecture seule."""

    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}
        self._callables: dict[str, Callable[..., ToolResult]] = {}
        self._frozen = False

    @property
    def frozen(self) -> bool:
        return self._frozen

    def register(self, module: ModuleType) -> ToolSpec:
        if self._frozen:
            raise RegistryFrozen("Registre gelé : aucun outil ne peut être ajouté.")
        spec = ToolSpec.from_mapping(module.SPEC)
        if spec.name in self._specs:
            raise ArgumentError(f"Outil déjà enregistré : {spec.name}")
        self._specs[spec.name] = spec
        self._callables[spec.name] = module.run
        return spec

    def freeze(self) -> "ToolRegistry":
        self._frozen = True
        return self

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._specs))

    def spec(self, name: str) -> ToolSpec:
        try:
            return self._specs[name]
        except KeyError as exc:
            raise UnknownTool(f"Outil inconnu : {name}") from exc

    def authorize(self, name: str, role: str) -> None:
        spec = self.spec(name)
        if role not in spec.authorized_roles:
            raise AuthorizationError(f"Rôle {role} non autorisé pour {name}")

    def validate(self, name: str, arguments: dict) -> dict:
        spec = self.spec(name)
        declared = {item.name: item for item in spec.arguments}
        unknown = sorted(set(arguments) - set(declared))
        if unknown:
            raise ArgumentError(f"{name} : arguments inconnus {unknown}")
        validated: dict[str, object] = {}
        for argument in spec.arguments:
            if argument.name not in arguments:
                if argument.required:
                    raise ArgumentError(f"{name} : argument requis absent {argument.name}")
                if argument.default is not None:
                    validated[argument.name] = argument.default
                continue
            validated[argument.name] = _check(name, argument, arguments[argument.name])
        return validated

    def call(
        self,
        name: str,
        arguments: dict,
        *,
        role: str,
        faults: dict | None = None,
    ) -> tuple[ToolResult, float]:
        """Exécute un outil validé et renvoie le résultat borné et la durée."""
        spec = self.spec(name)
        self.authorize(name, role)
        validated = self.validate(name, arguments)
        injected = (faults or {}).get(name, {})
        started = time.perf_counter()
        _apply_injected_delay(injected)
        if injected.get("error") == "unavailable":
            raise ToolUnavailable(f"{name} : source indisponible (injection de laboratoire)")
        if injected.get("error") == "timeout":
            raise ToolTimeout(f"{name} : délai dépassé (injection de laboratoire)")
        result = self._callables[name](validated, role=role)
        elapsed_ms = (time.perf_counter() - started) * 1000
        if elapsed_ms > spec.timeout_ms:
            raise ToolTimeout(f"{name} : {elapsed_ms:.0f} ms au-delà de {spec.timeout_ms} ms")
        poison_field = injected.get("poison_field")
        if poison_field:
            # Injection de laboratoire : un résultat d'outil transporte un texte
            # d'apparence impérative. Il reste une donnée, jamais une consigne.
            result = ToolResult(
                tool=result.tool,
                rows=tuple(
                    {**row, poison_field: injected.get("poison_value", "")}
                    for row in result.rows
                ),
                source=result.source,
                truncated=result.truncated,
                reason=result.reason,
            )
        if injected.get("empty"):
            result = ToolResult(
                tool=name, source=result.source,
                reason="résultat vide (injection de laboratoire)",
            )
        if len(result.rows) > spec.max_results:
            result = ToolResult(
                tool=result.tool,
                rows=result.rows[:spec.max_results],
                source=result.source,
                truncated=True,
                reason=result.reason,
            )
        return result, elapsed_ms


def _apply_injected_delay(injected: dict) -> None:
    delay_ms = int(injected.get("delay_ms", 0))
    if delay_ms > 0:
        time.sleep(min(delay_ms, 3000) / 1000)


def _check(tool: str, argument: ArgumentSpec, value: object) -> object:
    if argument.type == "string":
        if not isinstance(value, str):
            raise ArgumentError(f"{tool}.{argument.name} : chaîne attendue")
        if argument.min_length is not None and len(value) < argument.min_length:
            raise ArgumentError(f"{tool}.{argument.name} : chaîne trop courte")
        if argument.max_length is not None and len(value) > argument.max_length:
            raise ArgumentError(f"{tool}.{argument.name} : chaîne trop longue")
        if argument.pattern and not re.fullmatch(argument.pattern, value):
            raise ArgumentError(f"{tool}.{argument.name} : format invalide")
        return value
    if argument.type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ArgumentError(f"{tool}.{argument.name} : entier attendu")
        if argument.minimum is not None and value < argument.minimum:
            raise ArgumentError(f"{tool}.{argument.name} : valeur sous le minimum")
        if argument.maximum is not None and value > argument.maximum:
            raise ArgumentError(f"{tool}.{argument.name} : valeur au-dessus du maximum")
        return value
    if argument.type == "enum":
        if value not in argument.values:
            raise ArgumentError(f"{tool}.{argument.name} : valeur hors énumération")
        return value
    raise ArgumentError(f"{tool}.{argument.name} : type non supporté {argument.type}")


def default_registry() -> ToolRegistry:
    """Registre gelé des cinq outils de lecture distribués en M6."""
    from tools import diagnose, equipment, events, knowledge, maintenance

    registry = ToolRegistry()
    for module in (knowledge, equipment, events, maintenance, diagnose):
        registry.register(module)
    return registry.freeze()
