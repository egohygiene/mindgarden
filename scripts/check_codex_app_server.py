"""Probe a local Codex protocol in an isolated Linux process."""

from argparse import ArgumentParser
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import select
import shutil
from stat import S_ISREG
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic


MAX_STDOUT_BYTES = 8_192
MAX_SCHEMA_BYTES = 2_097_152
TIME_LIMIT = 10.0
VERSION_LINE = re.compile(rb"codex-cli (\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)\r?\n?")
SCHEMA_BUNDLE = "codex_app_server_protocol.schemas.json"
INITIALIZE = {
    "id": 1,
    "method": "initialize",
    "params": {
        "clientInfo": {"name": "mindgarden_protocol_probe", "version": "0.1.0"},
    },
}
INITIALIZED = {"method": "initialized", "params": {}}


class ProbeBlocked(Exception):
    """Fixed diagnostic code without raw process output or file locations."""


def sandbox_inputs(bwrap, codex, workspace):
    # Preserve inherited path values. Their host directories are never mounted.
    environment = {
        key: os.environ[key] for key in ("HOME", "CODEX_HOME") if os.environ.get(key)
    }
    if "HOME" not in environment:
        raise ProbeBlocked("home-path-unavailable")
    command = [
        bwrap,
        "--unshare-all",
        "--die-with-parent",
        "--new-session",
        "--dev",
        "/dev",
        "--proc",
        "/proc",
        "--ro-bind",
        str(codex),
        "/probe/codex",
        "--bind",
        str(workspace),
        "/work",
        "--size",
        "16777216",
        "--tmpfs",
        "/tmp",
    ]
    for value in sorted(set(environment.values())):
        path = PurePosixPath(value)
        if (
            not path.is_absolute()
            or path.anchor != "/"
            or len(path.parts) < 2
            or ".." in path.parts
            or any(
                path.is_relative_to(item)
                for item in ("/probe", "/proc", "/dev", "/work")
            )
        ):
            raise ProbeBlocked("home-path-unavailable")
        command.extend(("--dir", str(path)))
    command.extend(("--chdir", "/work", "--", "/probe/codex"))
    return command, environment


@contextmanager
def child(command, environment, *, writable=False):
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE if writable else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=environment,
            bufsize=0,
        )
    except OSError as error:
        raise ProbeBlocked("isolation-unavailable") from error
    try:
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired as error:
            raise ProbeBlocked("cleanup-timeout") from error
        finally:
            process.stdout.close()
            if process.stdin is not None:
                process.stdin.close()


def remaining(deadline):
    delay = deadline - monotonic()
    if delay <= 0:
        raise ProbeBlocked("timeout")
    return delay


def read_stdout(process, deadline, *, line=False, maximum=MAX_STDOUT_BYTES):
    result = bytearray()
    descriptor = process.stdout.fileno()
    while True:
        ready, _, _ = select.select([descriptor], [], [], remaining(deadline))
        if not ready:
            raise ProbeBlocked("timeout")
        part = os.read(descriptor, min(4096, maximum + 1 - len(result)))
        if not part:
            if line:
                raise ProbeBlocked("handshake-incomplete")
            return bytes(result)
        result.extend(part)
        if len(result) > maximum:
            raise ProbeBlocked("stdout-limit")
        if line and b"\n" in result:
            return bytes(result)


def successful_exit(process, deadline, diagnostic):
    try:
        if process.wait(timeout=remaining(deadline)) != 0:
            raise ProbeBlocked(diagnostic)
    except subprocess.TimeoutExpired as error:
        raise ProbeBlocked("timeout") from error


def command_stdout(command, environment, deadline, diagnostic):
    with child(command, environment) as process:
        output = read_stdout(process, deadline)
        successful_exit(process, deadline, diagnostic)
        return output


def schema_check(workspace):
    directory = workspace / "schema"
    path = directory / SCHEMA_BUNDLE
    try:
        if directory.is_symlink() or not S_ISREG(path.lstat().st_mode):
            raise ProbeBlocked("schema-unavailable")
        with path.open("rb") as stream:
            raw = stream.read(MAX_SCHEMA_BYTES + 1)
        if len(raw) > MAX_SCHEMA_BYTES:
            raise ProbeBlocked("schema-limit")
        definitions = json.loads(raw)["definitions"]
        for name, method in (
            ("ClientRequest", "initialize"),
            ("ClientNotification", "initialized"),
        ):
            if not any(
                option.get("properties", {}).get("method", {}).get("enum") == [method]
                for option in definitions[name]["oneOf"]
            ):
                raise ProbeBlocked("schema-incompatible")
        required = frozenset(definitions["InitializeResponse"]["required"])
        properties = definitions["InitializeResponse"]["properties"]
        if (
            not {"platformFamily", "platformOs", "userAgent"}
            <= required
            <= properties.keys()
        ):
            raise ProbeBlocked("schema-incompatible")
    except OSError as error:
        raise ProbeBlocked("schema-unavailable") from error
    except (ValueError, AttributeError, KeyError, TypeError, RecursionError) as error:
        raise ProbeBlocked("schema-incompatible") from error
    return hashlib.sha256(raw).hexdigest(), required


def handshake(command, environment, deadline, required_fields):
    with child(command, environment, writable=True) as process:
        try:
            process.stdin.write(
                json.dumps(INITIALIZE, separators=(",", ":")).encode() + b"\n"
            )
            raw = read_stdout(process, deadline, line=True)
            try:
                # Bounded unsolicited notifications can share a pipe read.
                # Only the first JSONL response participates in the handshake.
                response = json.loads(raw.partition(b"\n")[0])
            except (ValueError, RecursionError) as error:
                raise ProbeBlocked("handshake-incompatible") from error
            if (
                not isinstance(response, dict)
                or type(response.get("id")) is not int
                or response["id"] != INITIALIZE["id"]
                or "error" in response
                or not isinstance(response.get("result"), dict)
                or any(
                    not isinstance(response["result"].get(name), str)
                    for name in required_fields
                )
            ):
                raise ProbeBlocked("handshake-incompatible")
            process.stdin.write(
                json.dumps(INITIALIZED, separators=(",", ":")).encode() + b"\n"
            )
            process.stdin.close()
        except OSError as error:
            raise ProbeBlocked("handshake-incomplete") from error
        read_stdout(process, deadline, maximum=MAX_STDOUT_BYTES - len(raw))
        successful_exit(process, deadline, "handshake-incomplete")


def probe(codex_name, expected_version=None):
    if sys.platform != "linux" or not (bwrap := shutil.which("bwrap")):
        raise ProbeBlocked("isolation-unavailable")
    if not (codex_path := shutil.which(codex_name)):
        raise ProbeBlocked("codex-unavailable")
    deadline = monotonic() + TIME_LIMIT
    with TemporaryDirectory(prefix="mindgarden-codex-protocol-") as temporary:
        workspace = Path(temporary)
        command, environment = sandbox_inputs(
            bwrap, Path(codex_path).resolve(), workspace
        )
        raw_version = command_stdout(
            [*command, "--version"],
            environment,
            deadline,
            "isolation-unavailable",
        )
        match = VERSION_LINE.fullmatch(raw_version)
        if not match:
            raise ProbeBlocked("version-incompatible")
        version = match[1].decode("ascii")
        if expected_version is not None and version != expected_version:
            raise ProbeBlocked("version-mismatch")
        command_stdout(
            [*command, "app-server", "generate-json-schema", "--out", "/work/schema"],
            environment,
            deadline,
            "schema-unavailable",
        )
        schema_sha256, fields = schema_check(workspace)
        handshake(
            [
                *command,
                "app-server",
                "--listen",
                "stdio://",
                "-c",
                "analytics.enabled=false",
                "-c",
                "check_for_update_on_startup=false",
                "-c",
                'cli_auth_credentials_store="ephemeral"',
            ],
            environment,
            deadline,
            fields,
        )
    return {
        "status": "protocol-verified",
        "version": version,
        "schema_sha256": schema_sha256,
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--codex", default="codex", help="Trusted local standalone Codex executable"
    )
    parser.add_argument(
        "--expected-version", help="Require this exact Codex CLI version"
    )
    arguments = parser.parse_args()
    try:
        result = probe(arguments.codex, arguments.expected_version)
    except ProbeBlocked as error:
        result = {"status": "blocked", "reason": str(error)}
    except (OSError, RuntimeError, ValueError):
        result = {"status": "blocked", "reason": "local-probe-failed"}
    result.update(connected=False, account_checked=False, model_calls=0)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "protocol-verified" else 3


if __name__ == "__main__":
    raise SystemExit(main())
