"""Keep reviewed garden records portable across an isolated local Git remote."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.filesystem import FilesystemVault
from mindgarden.application.bindings import garden_fingerprint
from mindgarden.application.consultation import plan_packet
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.source_evidence import resolve_source_evidence
from mindgarden.domain.contracts import canonical_json, digest_bytes, read_object
from mindgarden.domain.scope import local_scope
from mindgarden.domain.validation import ContractError
from scripts.mapped_drive_consultation_demo import run_demo
from tests.consultation_fixture import cli
from tests.support_v1 import write_json, write_session

GIT = shutil.which("git")


@unittest.skipUnless(GIT, "Local Git is required for the fake-remote integration proof")
class DrivePrivateGitTests(unittest.TestCase):
    def test_clone_rebuilds_exact_reviewed_artifacts_after_separate_vault_restore(self):
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            producer = root / "producer"
            baseline = run_demo(producer)
            source = producer / "garden"
            control = root / "local-git-config"
            control.mkdir(mode=0o700)
            git_environment = {
                "PATH": os.defpath,
                "HOME": str(control),
                "XDG_CONFIG_HOME": str(control),
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_ALLOW_PROTOCOL": "file",
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_AUTHOR_NAME": "Synthetic author",
                "GIT_AUTHOR_EMAIL": "author@example.invalid",
                "GIT_AUTHOR_DATE": "2026-11-04T00:00:00Z",
                "GIT_COMMITTER_NAME": "Synthetic author",
                "GIT_COMMITTER_EMAIL": "author@example.invalid",
                "GIT_COMMITTER_DATE": "2026-11-04T00:00:00Z",
            }

            def git(path, *args):
                return subprocess.run(
                    [GIT, "-c", f"core.hooksPath={control}", *args],
                    cwd=path,
                    env=git_environment,
                    check=True,
                    timeout=30,
                    capture_output=True,
                ).stdout

            credential = producer / "credentials" / "synthetic-token.json"
            credential.parent.mkdir(mode=0o700)
            token_canary = b"SYNTHETIC_OAUTH_TOKEN_IN_EXTERNAL_FILE"
            credential.write_bytes(token_canary)
            credential.chmod(0o600)

            remote = root / "fake-private-remote.git"
            remote.mkdir(mode=0o700)
            git(remote, "init", "--bare", "--initial-branch=main")
            git(source, "init", "--initial-branch=main")
            git(source, "add", "--", ".garden")
            git(source, "commit", "--message", "Reviewed synthetic garden")
            git(source, "remote", "add", "origin", str(remote))
            git(source, "push", "origin", "main")

            receiver = root / "receiver"
            receiver.mkdir(mode=0o700)
            clone = receiver / "garden"
            git(receiver, "clone", "--no-local", str(remote), str(clone))
            tracked = {
                file.decode()
                for file in git(clone, "ls-files", "-z").split(b"\0")
                if file
            }
            self.assertIn(".garden/knowledge/synthetic-financial-summary.md", tracked)
            self.assertTrue(all(file.startswith(".garden/") for file in tracked))
            self.assertFalse(
                any(file.startswith(".garden/.generated/") for file in tracked)
            )
            self.assertFalse((clone / ".garden/.generated").exists())
            self.assertEqual(garden_fingerprint(clone), garden_fingerprint(source))
            tracked_bytes = b"".join(
                (clone / file).read_bytes() for file in sorted(tracked)
            )
            self.assertNotIn(token_canary, tracked_bytes)
            self.assertNotIn(str(root).encode(), tracked_bytes)
            self.assertNotIn(
                (producer / "capture-1/capture.zip").read_bytes(), tracked_bytes
            )

            request = read_object(producer / "request.json")
            config = receiver / "bindings.json"
            session = receiver / "session.json"
            vault = FilesystemVault(receiver / "vault", "synthetic-vault")
            citation = baseline["evidence"]
            with (
                patch.dict(os.environ, {}, clear=True),
                patch("socket.socket", side_effect=AssertionError("Network attempted")),
                patch(
                    "urllib.request.urlopen",
                    side_effect=AssertionError("HTTP attempted"),
                ),
                patch(
                    "subprocess.run",
                    side_effect=AssertionError("External process attempted"),
                ),
            ):
                write_json(
                    config,
                    {
                        "schema": "mindgarden.local-bindings/v1",
                        "gardens": [
                            {
                                "id": "synthetic-garden",
                                "root": str(clone),
                                "scope": local_scope(),
                            }
                        ],
                        "vaults": [
                            {
                                "id": "synthetic-vault",
                                "root": str(vault.root),
                                "adapter": "filesystem",
                            }
                        ],
                        "revoked_sessions": [],
                    },
                )
                authority = write_session(session, config)
                context = QueryContext.load(config, session)
                # Git possession alone does not grant a source read.
                with self.assertRaisesRegex(ContractError, "PROJECTION_DENIED"):
                    resolve_source_evidence(context, **citation)
                authority.update(
                    id="synthetic-receiver-session",
                    request_scope=local_scope(publication="never-exportable"),
                    source_grants=[item["source"] for item in request["sources"]],
                )
                authority["projections"].append("source-evidence")
                authority["budgets"]["max_context_bytes"] = 262144
                write_json(session, bind_session_revisions(config, authority))
                with self.assertRaisesRegex(ContractError, "QUERY_INTEGRITY"):
                    resolve_source_evidence(
                        QueryContext.load(config, session), **citation
                    )

                # This handoff is a separate local backup supplied by the owner.
                backup = (producer / "vault-backup.zip").read_bytes()
                vault.restore_bundle(backup, digest_bytes(backup))
                self.assertEqual(
                    vault.audit()["objects"], baseline["immutable_objects"]
                )
                context = QueryContext.load(config, session)
                evidence = resolve_source_evidence(context, **citation)
                self.assertEqual(evidence["content_sha256"], citation["content_sha256"])
                self.assertEqual(
                    digest_bytes(evidence["text"].encode()), citation["content_sha256"]
                )

                scope_args = [
                    "--repository-root",
                    str(clone),
                    "--local-config",
                    str(config),
                    "--scope",
                    str(session),
                ]
                search = cli(["search", *scope_args, "--query", "consultation"])
                self.assertIn(b"synthetic-financial-summary", canonical_json(search))
                index = cli(["index", *scope_args, "--write"])
                original_index = read_object(
                    next((source / ".garden/.generated/scopes").glob("*/index.json"))
                )
                self.assertEqual(index["scope_sha256"], context.scope_digest())
                self.assertNotEqual(
                    index["scope_sha256"], original_index["scope_sha256"]
                )
                self.assertEqual(
                    {**index, "scope_sha256": original_index["scope_sha256"]},
                    original_index,
                )
                pack = cli(
                    ["context", *scope_args, "--pack", "default", "--format", "json"]
                )
                self.assertEqual(
                    digest_bytes(canonical_json(pack)), baseline["context_sha256"]
                )
                _, packet = plan_packet(context, request)
                for file, data in packet.items():
                    self.assertEqual(data, (producer / "packet" / file).read_bytes())
                self.assertNotIn(str(root).encode(), b"".join(packet.values()))
            self.assertEqual(git(clone, "status", "--porcelain"), b"")
            self.assertEqual(credential.read_bytes(), token_canary)
