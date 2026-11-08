"""Synthetic tool-message adapter; recovery is independent of the first adapter."""

import json

DESCRIPTOR = {"id": "synthetic-tool-provider", "version": "1.0.0", "format": "tool-message-envelope",
              "limitations": ["No inference or proprietary history import.", "Tool content is evidence, never instruction authority."]}


def project(state):
    return json.dumps({"adapter": DESCRIPTOR["id"], "messages": [{"role": "tool", "name": "mindgarden-context",
        "content": json.dumps(state, sort_keys=True)}]}, sort_keys=True).encode("utf8")


def recover(wire):
    return json.loads(json.loads(wire)["messages"][0]["content"])
