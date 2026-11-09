"""Optional semantic intent, followed by ordinary authorized read services."""

from dataclasses import replace
import logging
import json
import os
from time import monotonic

from ..domain.contracts import canonical_json
from ..domain.semantic_decision import (
    DecisionSettings,
    WorkflowDecision,
    WorkflowJudgment,
    WORKFLOWS,
)
from ..domain.validation import ContractError
from .retrieval import search_payload, graph_payload, backlinks_payload

LOGGER = logging.getLogger("mindgarden.semantic_decision")


def suggest_read_workflow(
    request, *, settings=None, judge=None, allow_hosted=False, clock=monotonic
):
    settings = settings or DecisionSettings.from_environment(os.environ)
    started = clock()

    def finish(outcome, reason, judgment=None, route=None):
        decision = WorkflowDecision(outcome, reason, settings.model)
        if judgment is not None:
            decision = replace(
                decision,
                resolved_model=judgment.model,
                route=route,
                choice=judgment.choice,
                probabilities=dict(judgment.probabilities),
                choice_confidence=judgment.confidence,
                supported_probability=judgment.supported_probability,
            )
        decision = replace(
            decision, latency_ms=round(max(0, clock() - started) * 1000, 3)
        )
        # Deliberately excludes prompt text, keys, source IDs and provider exception bodies.
        LOGGER.info(
            "semantic_decision %s",
            json.dumps(decision.as_dict(), sort_keys=True),
            extra={"decision_metadata": decision.as_dict()},
        )
        return decision

    try:
        valid = isinstance(request, str) and len(request.encode("utf8")) <= 4096
    except UnicodeError:
        valid = False
    if not valid:
        raise ContractError(
            "SEMANTIC_INPUT: supply at most 4096 UTF-8 bytes of explicit request text"
        )
    if not request.strip():
        return finish("clarify", "missing-request")
    if not settings.enabled:
        return finish("disabled", "use-explicit-cli")
    if allow_hosted is not True:
        return finish("policy-denied", "explicit-hosted-request-permission-required")
    if judge is None:
        from ..adapters.typesafe_decisions import TypeSafeWorkflowJudge

        judge = TypeSafeWorkflowJudge(settings)
    try:
        state = judge.configuration_state()
        if state not in {"ready", "unconfigured", "sdk-unavailable", "disabled"}:
            raise ValueError("Unknown provider state")
        if state != "ready":
            return finish(
                "unconfigured" if state == "unconfigured" else "unavailable", state
            )
        answer = judge.judge_workflow(request)
        if not isinstance(answer, WorkflowJudgment):
            raise ValueError("Unsupported provider result")
        answer.validate()
        if (
            clock() - started
            > settings.timeout_seconds * (settings.max_retries + 1) + 0.5
        ):
            return finish("unavailable", "decision-deadline-exceeded")
    except Exception:
        return finish("unavailable", "provider-failure")
    # Noul is applicability, not a confidence field; a forced Choice can be high for an unsupported request.
    if answer.supported_probability <= settings.unsupported_at_most:
        return finish("unsupported", "no-supported-workflow", answer)
    probabilities = sorted(answer.probabilities.values(), reverse=True)
    if (
        answer.supported_probability < settings.supported_at_least
        or answer.probabilities[answer.choice] < settings.minimum_choice_probability
        or probabilities[0] - probabilities[1] < settings.minimum_margin
    ):
        return finish("clarify", "uncertain-or-ambiguous", answer)
    return finish("selected", "provisional-thresholds-met", answer, answer.choice)


def dispatch_read_workflow(
    context, decision, *, query=None, target=None, limit=10, depth=1
):
    """The caller supplies typed arguments and authority independently of Jev."""
    context.check_live()
    if (
        not isinstance(decision, WorkflowDecision)
        or decision.outcome != "selected"
        or decision.route not in WORKFLOWS
    ):
        return {"status": "not-executed", "reason": "no-selected-supported-workflow"}
    if (
        type(limit) is not int
        or not 1 <= limit <= 100
        or type(depth) is not int
        or not 0 <= depth <= 4
    ):
        raise ContractError(
            "SEMANTIC_ARGUMENTS: read limits must be explicit bounded integers"
        )
    if decision.route == "search":
        if not isinstance(query, str) or not query.strip():
            return {
                "status": "clarification-required",
                "reason": "explicit-query-required",
            }
        payload = search_payload(context, query, limit=limit)
    elif decision.route == "graph":
        if not isinstance(target, str) or not target:
            return {
                "status": "clarification-required",
                "reason": "explicit-target-required",
            }
        payload = graph_payload(context, start=target, depth=depth, limit=limit)
    else:
        if not isinstance(target, str) or not target:
            return {
                "status": "clarification-required",
                "reason": "explicit-target-required",
            }
        payload = backlinks_payload(context, target)
    context.ensure_output(canonical_json(payload))
    return payload
