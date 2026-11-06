"""Synthetic JSON adapter; no provider SDK, model or hidden memory."""

import json

DESCRIPTOR = {"id": "synthetic-json-provider", "version": "1.0.0", "format": "json-envelope",
              "limitations": ["No inference or proprietary history import.", "Only explicit scoped projections are available."]}


def project(state):
    return json.dumps({"adapter": DESCRIPTOR["id"], "payload": state}, sort_keys=True).encode("utf8")


def recover(wire):
    return json.loads(wire)["payload"]
