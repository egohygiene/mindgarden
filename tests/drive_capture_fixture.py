"""Synthetic provider with real filesystem storage, never a real Drive account."""

from copy import deepcopy
import hashlib

from mindgarden.application.bindings import LocalBindings
from mindgarden.application.storage import open_vault
from mindgarden.domain.drive_capture import FOLDER
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from tests.consultation_fixture import FIXTURES, cli
from tests.support_v1 import TIME, create_garden, write_json


class FixtureDrive:
    def __init__(self):
        self.data = {
            "file-a": (FIXTURES / "account-a.csv").read_bytes(),
            "file-overlap": (FIXTURES / "account-a-overlap.csv").read_bytes(),
            "file-b": (FIXTURES / "account-b.csv").read_bytes(),
        }
        self.items = {
            identity: {
                "id": identity,
                "name": identity + ".csv",
                "mimeType": "text/csv",
                "version": "1",
                "parents": ["selected-folder"],
                "size": str(len(raw)),
                "md5Checksum": hashlib.md5(raw, usedforsecurity=False).hexdigest(),
                "capabilities": {"canDownload": True},
            }
            for identity, raw in self.data.items()
        }
        self.items["selected-folder"] = {
            "id": "selected-folder",
            "name": "Synthetic selected folder",
            "mimeType": FOLDER,
            "version": "1",
            "parents": [],
            "capabilities": {},
        }
        self.reads, self.calls = [], []
        self.fail = None
        self.change_on_read = False

    def stat(self, identity):
        self.calls.append(("stat", identity))
        if identity not in self.items:
            raise ContractError("CAPTURE_MISSING: synthetic selected input unavailable")
        return deepcopy(self.items[identity])

    def children(self, identity):
        self.calls.append(("children", identity))
        return [
            deepcopy(item)
            for item in self.items.values()
            if identity in item.get("parents", [])
        ]

    def read(self, item, media_type):
        identity = item["id"]
        self.reads.append(identity)
        if self.fail == identity:
            raise ContractError("CAPTURE_UNAVAILABLE: synthetic provider failure")
        if self.change_on_read:
            self.items[identity]["version"] = "2"
        return self.data[identity]


def create_capture_fixture(root):
    root.mkdir(parents=True, exist_ok=True)
    garden = root / "garden"
    create_garden(garden)
    config = root / "bindings.json"
    write_json(
        config,
        {
            "schema": "mindgarden.local-bindings/v1",
            "gardens": [
                {"id": "synthetic-garden", "root": str(garden), "scope": local_scope()}
            ],
            "vaults": [
                {
                    "id": "synthetic-vault",
                    "root": str(root / "vault"),
                    "adapter": "filesystem",
                }
            ],
            "revoked_sessions": [],
        },
    )
    args = [
        "vault",
        "init",
        "--local-config",
        str(config),
        "--vault-id",
        "synthetic-vault",
    ]
    planned = cli(args)
    cli(args + ["--apply", "--plan-digest", planned["plan_sha256"]])
    binding = {
        "schema": "mindgarden.drive-binding/v1",
        "id": "synthetic-drive-collection",
        "captured_at": TIME,
        "folders": ["selected-folder"],
        "file_ids": [],
        "recursive": False,
        "media_types": ["text/csv"],
        "exports": [],
        "scope": local_scope(
            execution="controlled-import", publication="never-exportable"
        ),
        "review_authority": {"kind": "human", "id": "synthetic-reviewer"},
        "review": {
            "state": "approved",
            "reviewers": ["synthetic-reviewer"],
            "reviewed_at": TIME,
            "rationale": "Explicit synthetic selection/ordinary classification, not knowledge approval.",
        },
        "limits": {
            "max_files": 16,
            "max_depth": 2,
            "max_bytes": 100000,
            "max_file_bytes": 20000,
            "max_requests": 100,
            "max_seconds": 60,
            "timeout_seconds": 5,
        },
    }
    binding_path = root / "drive.json"
    write_json(binding_path, binding)
    return {
        "root": root,
        "garden": garden,
        "configuration": config,
        "binding": binding,
        "binding_path": binding_path,
        "vault": open_vault(LocalBindings.load(config), "synthetic-vault"),
        "provider": FixtureDrive(),
    }
