"""Closed read-workflow judgments; model answers carry no execution authority."""

from dataclasses import dataclass, field
from math import isfinite
from typing import Literal, Mapping, Protocol

from .validation import ContractError

Workflow = Literal["search", "graph", "backlinks"]
Outcome = Literal[
    "selected",
    "clarify",
    "unsupported",
    "disabled",
    "unconfigured",
    "unavailable",
    "policy-denied",
]
WORKFLOWS = {
    "search": "Find reviewed knowledge matching explicit words or a topic; return cited search results.",
    "graph": "Explore connections reachable from an explicitly identified knowledge item.",
    "backlinks": "List knowledge items that link to an explicitly identified knowledge item.",
}


@dataclass(frozen=True)
class DecisionSettings:
    enabled: bool = False
    model: str = "jev-latest"
    timeout_seconds: float = 3.0
    max_retries: int = 0
    minimum_choice_probability: float = 0.85
    minimum_margin: float = 0.15
    unsupported_at_most: float = 0.2
    supported_at_least: float = 0.8

    def __post_init__(self):
        numbers = (
            self.timeout_seconds,
            self.minimum_choice_probability,
            self.minimum_margin,
            self.unsupported_at_most,
            self.supported_at_least,
        )
        if (
            type(self.enabled) is not bool
            or not isinstance(self.model, str)
            or not self.model.strip()
            or len(self.model) > 120
            or any(type(n) not in (int, float) or not isfinite(n) for n in numbers)
            or not 0.1 <= self.timeout_seconds <= 10
            or type(self.max_retries) is not int
            or not 0 <= self.max_retries <= 1
            or not 0 <= self.unsupported_at_most < self.supported_at_least <= 1
            or not 0 <= self.minimum_choice_probability <= 1
            or not 0 <= self.minimum_margin <= 1
        ):
            raise ContractError(
                "SEMANTIC_CONFIG: require bounded explicit decision settings"
            )

    @classmethod
    def from_environment(cls, environ):
        enabled = environ.get("TYPESAFE_ENABLED", "false").strip().lower()
        if enabled not in {"true", "false", "1", "0"}:
            raise ContractError(
                "SEMANTIC_CONFIG: TYPESAFE_ENABLED must be true/false or 1/0"
            )
        if enabled in {"false", "0"}:
            return cls()
        try:
            return cls(
                enabled=enabled in {"true", "1"},
                model=environ.get("TYPESAFE_MODEL", "jev-latest"),
                timeout_seconds=float(environ.get("TYPESAFE_TIMEOUT_SECONDS", "3")),
                max_retries=int(environ.get("TYPESAFE_MAX_RETRIES", "0")),
            )
        except (ValueError, TypeError) as error:
            raise ContractError(
                "SEMANTIC_CONFIG: invalid bounded provider configuration"
            ) from error


@dataclass(frozen=True)
class WorkflowJudgment:
    model: str
    choice: str
    probabilities: Mapping[str, float]
    confidence: float
    supported_probability: (
        float  # Noul: P(the request fits a supported workflow), no confidence field.
    )

    def validate(self):
        values = [
            self.confidence,
            self.supported_probability,
            *self.probabilities.values(),
        ]
        if (
            not isinstance(self.model, str)
            or not self.model
            or len(self.model) > 200
            or self.choice not in WORKFLOWS
            or set(self.probabilities) != set(WORKFLOWS)
            or any(
                type(n) not in (int, float) or not isfinite(n) or not 0 <= n <= 1
                for n in values
            )
            or abs(sum(self.probabilities.values()) - 1) > 0.00001
            or self.probabilities[self.choice] != max(self.probabilities.values())
        ):
            raise ContractError(
                "SEMANTIC_RESPONSE: invalid closed-set probability result"
            )
        return self


class WorkflowJudge(Protocol):
    def configuration_state(self) -> str: ...
    def judge_workflow(self, request: str) -> WorkflowJudgment: ...


@dataclass(frozen=True)
class WorkflowDecision:
    outcome: Outcome
    reason: str
    requested_model: str
    resolved_model: str | None = None
    route: Workflow | None = None
    choice: str | None = None
    probabilities: Mapping[str, float] = field(default_factory=dict)
    choice_confidence: float | None = None
    supported_probability: float | None = None
    latency_ms: float = 0.0
    decision_id: str = "mindgarden.read-workflow/v1"

    def as_dict(self):
        return {
            "decision_id": self.decision_id,
            "outcome": self.outcome,
            "reason": self.reason,
            "requested_model": self.requested_model,
            "resolved_model": self.resolved_model,
            "route": self.route,
            "choice": self.choice,
            "probabilities": dict(self.probabilities),
            "choice_confidence": self.choice_confidence,
            "supported_probability": self.supported_probability,
            "latency_ms": self.latency_ms,
            "fallback": "explicit-cli"
            if self.outcome
            in {"disabled", "unconfigured", "unavailable", "policy-denied"}
            else "clarification"
            if self.outcome == "clarify"
            else "unsupported"
            if self.outcome == "unsupported"
            else "supported-read-handler",
        }
