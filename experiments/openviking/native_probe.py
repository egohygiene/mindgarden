"""Bounded native preflight with explicit synthetic config and no model download.

A blocked service is evidence of a gap, never a passing retrieval benchmark.
"""

import argparse
import asyncio
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import faulthandler
import tempfile
import time
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--runtime-directory", type=Path)
    args = parser.parse_args()
    if not args.worker:
        return supervise(args)
    started = time.perf_counter()
    attempts = []
    result = {
        "schema": "mindgarden.openviking-native-observation/v1",
        "observed_at": "2026-11-07",
        "native_version": importlib.metadata.version("openviking"),
        "sdk_version": importlib.metadata.version("openviking-sdk"),
        "model_calls_completed": 0,
        "service_listen_started": False,
        "confidential_runtime_verified": False,
        "retrieval_comparison": "blocked",
        "native_syscall_trace": "unavailable: sandbox denies ptrace",
    }
    root = args.runtime_directory
    if (
        root is None
        or root.exists()
        or any(p.is_symlink() for p in (root, *root.parents))
    ):
        parser.error("worker requires a new ordinary owned runtime directory")
    root.mkdir(parents=True, exist_ok=False)
    private_trace = (root / "trace.log").open("w")
    faulthandler.dump_traceback_later(12, file=private_trace)
    if True:
        config_path = root / "ov.conf"
        client_path = root / "ovcli.conf"
        config = {
            "storage": {"workspace": str(root / "data")},
            "embedding": {
                "dense": {
                    "provider": "local",
                    "model": "bge-small-zh-v1.5-f16",
                    "model_path": str(root / "missing-model.gguf"),
                    "cache_dir": str(root / "models"),
                }
            },
            "vlm": {
                "provider": "openai",
                "model": "synthetic-unavailable",
                "api_key": "synthetic-not-a-secret",
                "api_base": "http://127.0.0.1:9/v1",
            },
            "telemetry": {"tracer": {"enabled": False}},
            "log": {"level": "WARNING", "output": str(root / "native.log")},
            "server": {"host": "127.0.0.1", "port": 1933},
        }
        config_path.write_text(json.dumps(config))
        client_path.write_text(
            json.dumps(
                {"url": "http://127.0.0.1:9", "api_key": "synthetic-not-a-secret"}
            )
        )
        env = {
            "OPENVIKING_CONFIG_FILE": str(config_path),
            "OPENVIKING_CLI_CONFIG_FILE": str(client_path),
            "OPENVIKING_ENABLE_RECORDER": "false",
            "XDG_CACHE_HOME": str(root / "cache"),
            "HF_HOME": str(root / "huggingface"),
            "TOKENIZERS_PARALLELISM": "false",
        }

        def progress(stage):
            result["last_stage"] = stage
            result["python_http_attempts"] = attempts
            args.report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")

        progress("explicit-owned-config-written")

        def deny(*_args, **_kwargs):
            attempts.append("blocked-python-http-request")
            progress("python-http-request-blocked")
            raise RuntimeError(
                "Experiment forbids provider/download/telemetry requests"
            )

        with (
            patch.dict(os.environ, env),
            patch("requests.sessions.Session.request", side_effect=deny),
            patch("httpx.Client.request", side_effect=deny),
            patch("httpx.AsyncClient.request", side_effect=deny),
        ):
            progress("before-native-import")
            import openviking

            progress("native-module-imported")
            from openviking_cli.utils.config.open_viking_config import OpenVikingConfig
            from openviking.server.config import ServerConfig

            progress("native-config-classes-imported")
            config_object = OpenVikingConfig.from_dict(config)
            progress("explicit-native-config-parsed")
            result["python_facade"] = {
                "embedded_OpenViking": hasattr(openviking, "OpenViking"),
                "SyncHTTPClient": hasattr(openviking, "SyncHTTPClient"),
            }
            result["config"] = {
                "tracing_enabled": config_object.telemetry.tracer.enabled,
                "local_model": config_object.embedding.dense.model,
                "storage_workspace_owned": Path(
                    config_object.storage.workspace
                ).is_relative_to(root),
                "server_default_host": ServerConfig().host,
                "server_default_port": ServerConfig().port,
            }
            unknown = OpenVikingConfig.from_dict(
                {**config, "mindgarden_required_scope": "restricted-canary"}
            )
            result["unknown_policy_field_preserved"] = (
                "mindgarden_required_scope" in unknown.model_dump()
            )
            assert not result["unknown_policy_field_preserved"]
            progress("before-explicit-missing-model-preflight")
            try:
                config_object.embedding.get_embedder()
                result["embedding_preflight"] = "unexpected-success"
            except Exception as error:
                result["embedding_preflight"] = {
                    "status": "blocked",
                    "error_type": type(error).__name__,
                    "reason": "Explicit local model file unavailable; no default downloader allowed.",
                }

            async def service_probe():
                from openviking.service.core import OpenVikingService

                service = None
                try:
                    service = OpenVikingService(path=str(root / "data"))
                    result["service_constructor"] = "passed"
                    progress("service-constructor-completed")
                    progress("before-service-initialization")
                    await asyncio.wait_for(service.initialize(), timeout=15)
                    result["service_initialization"] = "passed"
                except Exception as error:
                    result["service_initialization"] = {
                        "status": "blocked",
                        "error_type": type(error).__name__,
                        "reason": "See owned local log; no private source/model/provider is supplied.",
                    }
                    progress("service-initialization-result")
                finally:
                    if service is not None:
                        progress("before-partial-service-close")
                        try:
                            await asyncio.wait_for(service.close(), timeout=5)
                            result["partial_service_close"] = "passed"
                        except Exception as error:
                            result["partial_service_close"] = type(error).__name__

            progress("before-service-construction")
            asyncio.run(service_probe())
            progress("service-attempt-completed")
        result["python_http_attempts"] = attempts
        result["model_file_created"] = (root / "missing-model.gguf").exists()
        result["owned_runtime_bytes"] = sum(
            p.stat().st_size for p in root.rglob("*") if p.is_file()
        )
        result["owned_runtime_file_count"] = sum(p.is_file() for p in root.rglob("*"))
        result["generated_models"] = (
            sum(p.is_file() for p in (root / "models").rglob("*"))
            if (root / "models").exists()
            else 0
        )
        assert not result["model_file_created"] and result["generated_models"] == 0
    result["temporary_runtime_removed"] = False
    faulthandler.cancel_dump_traceback_later()
    private_trace.close()
    result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
    result["max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result["limitations"] = [
        "Python HTTP guards and a network-denied sandbox do not prove every native egress/telemetry path.",
        "No model or encrypted runtime supplied; quality, live ingestion/retrieval/session-memory and service backup/upgrade remain unverified.",
        "Owned temporary-runtime cleanup is not a production erasure guarantee.",
    ]
    args.report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


def supervise(arguments):
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="mindgarden-openviking-supervised-") as tmp:
        root = Path(tmp)
        report = root / "partial.json"
        try:
            process = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "experiments.openviking.native_probe",
                    "--worker",
                    "--runtime-directory",
                    str(root / "runtime"),
                    "--report",
                    str(report),
                ],
                capture_output=True,
                text=True,
                timeout=25,
            )
            status = "worker-completed" if process.returncode == 0 else "worker-failed"
        except subprocess.TimeoutExpired:
            status = "blocked-timeout"
        result = (
            json.loads(report.read_text())
            if report.exists()
            else {
                "schema": "mindgarden.openviking-native-observation/v1",
                "last_stage": "before-progress-report",
            }
        )
        result["probe_status"] = status
        result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
        result["max_child_rss_kib"] = resource.getrusage(
            resource.RUSAGE_CHILDREN
        ).ru_maxrss
        result["owned_runtime_bytes"] = sum(
            p.stat().st_size for p in root.rglob("*") if p.is_file()
        )
        trace = root / "runtime/trace.log"
        if trace.exists():
            # Private troubleshooting evidence stays outside portable/public records.
            Path(".cache/evaluations/openviking-timeout-stack.log").write_text(
                trace.read_text()
            )
        result["retrieval_comparison"] = "blocked"
        result["limitations"] = [
            "No native retrieval/quality/session/backup/upgrade proof; startup did not establish a usable no-model service.",
            "Python HTTP guards and network-denied sandbox do not prove every native egress/telemetry path.",
            "Owned lab cleanup is not production erasure or encrypted-runtime assurance.",
        ]
    result["temporary_runtime_removed"] = not root.exists()
    arguments.report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
