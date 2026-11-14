"""Private create-or-verify projection bundles; canonical sources are never targets."""

import os
from pathlib import Path
import re

from .registry_files import control_path, private_parent, read_control
from ..domain.contracts import canonical_json, digest_bytes, safe_path
from ..domain.validation import ContractError

MARKER = ".mindgarden-generated.json"


def inventory(files):
    return [
        {"path": name, "sha256": digest_bytes(content), "size_bytes": len(content)}
        for name, content in sorted(files.items())
    ]


def complete_generated(files, current_digest):
    """Expose the exact owned inventory for side-effect-free budget checks."""
    files = dict(files)
    if (
        MARKER in files
        or len(files) > 256
        or sum(map(len, files.values())) > 16 * 1024 * 1024
    ):
        raise ContractError(
            "GENERATED_BUDGET: invalid or oversized projection inventory"
        )
    for name in files:
        if len(Path(name).parts) != 1:
            raise ContractError(
                "GENERATED_PATH: flat portable output names are required"
            )
        if any(character in name for character in ("\\", ":", "\x00")):
            raise ContractError("PATH_UNSAFE: use a relative POSIX path")
        if name == "..":
            raise ContractError("PATH_UNSAFE: path must stay within its declared root")
    complete = {
        **files,
        MARKER: canonical_json(
            {
                "schema": "mindgarden.generated-bundle/v1",
                "plan_sha256": current_digest,
                "publication": "never-exportable",
                "files": inventory(files),
            }
        ),
    }
    return complete


def apply_generated(
    directory,
    files,
    reviewed_digest,
    current_digest,
    *,
    check_live,
    verify_inputs,
    validate_output=None,
):
    if reviewed_digest != current_digest:
        raise ContractError(
            "GENERATED_PLAN_STALE: review current source, policy, request and output digests"
        )
    complete = complete_generated(files, current_digest)
    files = dict(files)
    for name in files:
        safe_path(directory, name)
    if validate_output is not None:
        validate_output(complete)
    control_path(directory / MARKER)
    private_parent(directory.parent / (directory.name + ".control"))
    check_live()
    verify_inputs()
    if directory.exists():
        if set(p.name for p in directory.iterdir()) != set(complete):
            raise ContractError(
                "GENERATED_CONFLICT: preserve existing output and choose a new private directory"
            )
        for name, content in complete.items():
            path = safe_path(directory, name)
            if not path.is_file() or path.read_bytes() != content:
                raise ContractError(
                    "GENERATED_CONFLICT: existing projection differs; retain it for review"
                )
        check_live()
        verify_inputs()
        return False
    # Partial attempts remain inspectable; no implicit repair or source deletion.
    directory.mkdir(mode=0o700)
    for name in sorted(files) + [MARKER]:
        check_live()
        verify_inputs()
        with safe_path(directory, name).open("xb") as output:
            os.chmod(output.name, 0o600)
            output.write(complete[name])
            output.flush()
            os.fsync(output.fileno())
    check_live()
    verify_inputs()
    return True


def verify_generated(
    directory, files, *, check_live, verify_inputs, validate_output=None
):
    """Verify current authorized bytes without adopting an old plan's authority.

    Session renewal can change a plan digest without changing its output. The
    retained marker identifies the old owned inventory; current recomputation,
    source verification and live authority determine whether these bytes match.
    This function never creates, repairs, chmods or overwrites output.
    """
    from ..domain.contracts import strict_json

    check_live()
    verify_inputs()
    marker_bytes = read_control(directory / MARKER)
    marker = strict_json(marker_bytes)
    if (
        not isinstance(marker, dict)
        or not isinstance(marker.get("plan_sha256"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", marker["plan_sha256"])
    ):
        raise ContractError(
            "GENERATED_CONFLICT: prior ownership metadata is incompatible; retain it for inspection"
        )
    complete = complete_generated(files, marker["plan_sha256"])
    if marker_bytes != complete[MARKER]:
        raise ContractError(
            "GENERATED_CONFLICT: existing inventory differs from current authorized output"
        )
    if validate_output is not None:
        validate_output(complete)
    try:
        if set(path.name for path in directory.iterdir()) != set(complete):
            raise ContractError(
                "GENERATED_CONFLICT: preserve unexpected or incomplete output for review"
            )
        for name, content in complete.items():
            check_live()
            if read_control(safe_path(directory, name)) != content:
                raise ContractError(
                    "GENERATED_CONFLICT: existing projection differs; retain it for review"
                )
    except OSError as error:
        raise ContractError(
            "GENERATED_CONFLICT: selected output cannot be verified; retain it for review"
        ) from error
    check_live()
    verify_inputs()
