"""Replaceable deterministic scheduling examples; no learning-effect claim."""

from datetime import datetime, timedelta
from typing import Protocol

from .contracts import ContractRegistry, canonical_json, digest_bytes
from .validation import ContractError


class Scheduler(Protocol):
    def advance(self, stage: int, grade: str) -> int: ...
    def interval_days(self, stage: int) -> int: ...


class FixedIntervals:
    def __init__(self, intervals):
        self.intervals = intervals

    def advance(self, stage, grade):
        change = {"again": -stage, "hard": -1, "good": 1, "easy": 2}[grade]
        return min(len(self.intervals) - 1, max(0, stage + change))

    def interval_days(self, stage):
        return self.intervals[stage]


def default_schedulers():
    return {
        ("fixed-intervals", "1.0.0"): FixedIntervals((1, 3, 7, 14, 30, 60)),
        ("fixed-intervals", "2.0.0"): FixedIntervals((1, 2, 5, 10, 21, 45)),
    }


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def item_revision(item):
    return "sha256:" + digest_bytes(canonical_json(item))


def schedule_items(items, history, profile, *, as_of, now, schedulers=None):
    registry = default_schedulers() if schedulers is None else schedulers
    selected = (profile["id"], profile["version"])
    if selected not in registry:
        raise ContractError(
            "LEARNING_SCHEDULER: declared scheduler/version is unavailable"
        )
    contracts = ContractRegistry()
    by_id = {item["id"]: item for item in items}
    seen = set()
    chains = {}
    stages = {}
    last = {}
    last_current = {}
    historical = []
    for event in history["events"]:
        if (
            contracts.errors(event, "learning-review-event")
            or event["id"] in seen
            or event["item"] not in by_id
        ):
            raise ContractError(
                "LEARNING_HISTORY: incompatible event or item identity; no partial history emitted"
            )
        seen.add(event["id"])
        identity = event["item"]
        if (
            event["previous_event"] != chains.get(identity)
            or timestamp(event["reviewed_at"]) > now
        ):
            raise ContractError(
                "LEARNING_HISTORY: event chain or review time is invalid"
            )
        if identity in last and timestamp(event["reviewed_at"]) < timestamp(
            last[identity]["reviewed_at"]
        ):
            raise ContractError(
                "LEARNING_HISTORY: review events must remain in chronological order"
            )
        algorithm = (event["scheduler"]["id"], event["scheduler"]["version"])
        if algorithm not in registry:
            raise ContractError(
                "LEARNING_SCHEDULER: historical algorithm/version is unavailable"
            )
        chains[identity] = event["id"]
        last[identity] = event
        if event["item_revision"] != item_revision(by_id[identity]):
            historical.append(
                {
                    "event": event["id"],
                    "item": identity,
                    "state": "historical-item-revision",
                }
            )
            continue
        if timestamp(event["reviewed_at"]) > timestamp(as_of):
            historical.append(
                {"event": event["id"], "item": identity, "state": "after-view-as-of"}
            )
            continue
        last_current[identity] = event
        state = stages.get(identity, 0)
        stages[identity] = registry[algorithm].advance(state, event["grade"])
    schedules = []
    for identity, item in sorted(by_id.items()):
        if (
            item["lifecycle"] != "approved"
            or item["schema"] != "mindgarden.learning-card/v1"
        ):
            continue
        stage = stages.get(identity, 0)
        event = last_current.get(identity)
        current = event is not None and event["item_revision"] == item_revision(item)
        anchor = event["reviewed_at"] if current else profile["anchor"]
        days = registry[selected].interval_days(stage)
        if type(days) is not int or not 1 <= days <= 3650:
            raise ContractError(
                "LEARNING_SCHEDULER: interval is outside the supported bound"
            )
        due = timestamp(anchor) + timedelta(days=days)
        reason = "initial-or-edited-item" if not current else "review:" + event["grade"]
        if current and event["scheduler"] != {
            "id": profile["id"],
            "version": profile["version"],
        }:
            reason = "explicit-scheduler-upgrade"
        schedules.append(
            {
                "schema": "mindgarden.learning-schedule/v1",
                "item": identity,
                "item_revision": item_revision(item),
                "algorithm": {"id": profile["id"], "version": profile["version"]},
                "stage": stage,
                "interval_days": days,
                "due_at": due.isoformat().replace("+00:00", "Z"),
                "due": due <= timestamp(as_of),
                "view_as_of": as_of,
                "reason": reason,
                "last_event": event["id"] if current else None,
            }
        )
    return schedules, historical
