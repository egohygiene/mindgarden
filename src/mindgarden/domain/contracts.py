"""Offline validation of the explicitly supported local JSON Schema vocabulary.

This is not a general JSON Schema implementation. Unknown keywords and remote
references are rejected, and the conformance tests compare the shipped contracts
with the development-only Draft 2020-12 validator.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import urlparse

from .validation import ContractError


def canonical_json(value: object) -> bytes:
    """Serialize portable records deterministically, without permissive numbers."""
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def strict_json(value: str | bytes) -> object:
    """Reject duplicate keys and non-JSON numeric constants without echoing data."""
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in items:
            if key in result:
                raise ContractError("JSON_DUPLICATE_KEY: duplicate object member")
            result[key] = item
        return result

    def invalid_constant(_value: str) -> None:
        raise ContractError("JSON_NUMBER: non-finite JSON number")

    def finite_float(raw: str) -> float:
        number = float(raw)
        if not math.isfinite(number):
            invalid_constant(raw)
        return number

    try:
        result = json.loads(value, object_pairs_hook=pairs, parse_constant=invalid_constant,
                            parse_float=finite_float)
        # Also reject escaped unpaired surrogates, which are not portable UTF-8.
        json.dumps(result, ensure_ascii=False).encode("utf8")
        return result
    except ContractError:
        raise
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ContractError("JSON_INVALID: expected strict UTF-8 JSON") from error


def read_object(path: Path) -> dict[str, object]:
    if path.stat().st_size > 2_000_000:
        raise ContractError("RECORD_OVERSIZED: metadata exceeds 2000000 bytes")
    value = strict_json(path.read_bytes())
    if not isinstance(value, dict):
        raise ContractError("JSON_OBJECT: expected an object")
    return value


def safe_path(root: Path, value: str) -> Path:
    """Resolve a portable relative path, checking every existing component."""
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or "\x00" in value):
        raise ContractError("PATH_UNSAFE: use a relative POSIX path")
    portable = PurePosixPath(value)
    if portable.is_absolute() or ".." in portable.parts or value in {".", ""}:
        raise ContractError("PATH_UNSAFE: path must stay within its declared root")
    target = root
    if root.is_symlink():
        raise ContractError("PATH_SYMLINK: declared root is a symlink")
    for part in portable.parts:
        target = target / part
        if target.is_symlink():
            raise ContractError("PATH_SYMLINK: path crosses a symlink")
    return target


@dataclass(frozen=True)
class Diagnostic:
    code: str
    location: str
    message: str
    remediation: str
    severity: str = "error"

    def document(self) -> dict[str, str]:
        return asdict(self)


KEYWORDS = {
    "$schema", "$id", "$ref", "$defs", "$comment", "title", "description",
    "default", "examples", "type", "const", "enum", "properties", "required",
    "additionalProperties", "patternProperties", "items", "minItems", "maxItems",
    "uniqueItems", "minLength", "maxLength", "pattern", "format", "minimum",
    "maximum", "allOf", "anyOf", "oneOf", "not", "if", "then", "else",
}


def contract_directory() -> Path:
    candidates = [Path(__file__).resolve().parents[3] / "contracts/v1",
                  Path(sys.prefix) / "share/mindgarden/contracts/v1"]
    for candidate in candidates:
        if (candidate / "common.schema.json").is_file():
            return candidate
    raise ContractError("CONTRACT_UNAVAILABLE: install the complete Mindgarden package")


class ContractRegistry:
    """A closed, local-only registry; validation never downloads a schema."""

    def __init__(self, directory: Path | None = None) -> None:
        self.schemas = {str(value["$id"]): value for value in
                        (read_object(path) for path in sorted(
                            (directory or contract_directory()).glob("*.schema.json")))}
        for schema in self.schemas.values():
            self._check_vocabulary(schema)

    def _check_vocabulary(self, schema: object) -> None:
        if isinstance(schema, bool):
            return
        if not isinstance(schema, dict) or set(schema) - KEYWORDS:
            raise ContractError("CONTRACT_UNSUPPORTED: schema vocabulary is not supported")
        if schema.get("format") not in {None, "uri", "date", "date-time"}:
            raise ContractError("CONTRACT_UNSUPPORTED: schema format is not supported")
        for field in ("properties", "patternProperties", "$defs"):
            for child in schema.get(field, {}).values():
                self._check_vocabulary(child)
        for field in ("items", "additionalProperties", "not", "if", "then", "else"):
            if field in schema:
                self._check_vocabulary(schema[field])
        for field in ("allOf", "anyOf", "oneOf"):
            for child in schema.get(field, []):
                self._check_vocabulary(child)

    def resolve(self, reference: str, base: dict) -> tuple[object, dict]:
        name, _, fragment = reference.partition("#")
        target = self.schemas.get(name) if name else base
        if target is None:
            raise ContractError("CONTRACT_REFERENCE: schema reference is not local")
        document = target
        if fragment:
            if not fragment.startswith("/"):
                raise ContractError("CONTRACT_REFERENCE: unsupported schema fragment")
            for token in fragment[1:].split("/"):
                target = target[token.replace("~1", "/").replace("~0", "~")]
        return target, document

    def errors(self, value: object, contract: str) -> list[Diagnostic]:
        local = contract.removeprefix("mindgarden.")
        name = contract if contract.startswith("urn:") else (
            "urn:egohygiene:mindgarden:" + local.replace("/v1", ":v1")
            + (":v1" if "/" not in local else ""))
        if name not in self.schemas:
            return [Diagnostic("CONTRACT_UNSUPPORTED", "$", "Unsupported record contract",
                               "Use an explicitly supported schema version.")]
        return self._errors(value, self.schemas[name], self.schemas[name], "$")

    def _errors(self, value: object, schema: object, base: dict, location: str) -> list[Diagnostic]:
        errors: list[Diagnostic] = []

        def fail(code: str, message: str, field: str = location) -> None:
            errors.append(Diagnostic("SCHEMA_" + code, field, message,
                                     "Correct the field according to the declared contract."))

        if schema is True:
            return []
        if schema is False:
            fail("FORBIDDEN", "Field is not permitted")
            return errors
        if "$ref" in schema:
            target, document = self.resolve(schema["$ref"], base)
            errors += self._errors(value, target, document, location)
        expected = schema.get("type")
        types = {"null": value is None, "boolean": isinstance(value, bool),
                 "integer": (isinstance(value, int) and not isinstance(value, bool))
                 or (isinstance(value, float) and value.is_integer()),
                 "number": isinstance(value, (int, float)) and not isinstance(value, bool),
                 "string": isinstance(value, str), "array": isinstance(value, list),
                 "object": isinstance(value, dict)}
        if expected and not any(types.get(item, False) for item in
                                (expected if isinstance(expected, list) else [expected])):
            fail("TYPE", "Incorrect field type")
            return errors
        if "const" in schema and canonical_json(value) != canonical_json(schema["const"]):
            fail("CONST", "Field does not match the required constant")
        if "enum" in schema and not any(canonical_json(value) == canonical_json(item)
                                         for item in schema["enum"]):
            fail("ENUM", "Field is outside the supported vocabulary")
        for child in schema.get("allOf", []):
            errors += self._errors(value, child, base, location)
        for field, minimum, maximum in (("anyOf", 1, None), ("oneOf", 1, 1)):
            if field in schema:
                valid = sum(not self._errors(value, child, base, location)
                            for child in schema[field])
                if valid < minimum or (maximum is not None and valid > maximum):
                    fail(field.upper(), "Field does not match a supported alternative")
        if "not" in schema and not self._errors(value, schema["not"], base, location):
            fail("NOT", "Field matches a prohibited form")
        if "if" in schema:
            branch = "else" if self._errors(value, schema["if"], base, location) else "then"
            if branch in schema:
                errors += self._errors(value, schema[branch], base, location)
        if isinstance(value, dict):
            for field in schema.get("required", []):
                if field not in value:
                    fail("REQUIRED", "Required field is missing", location + "/" + field)
            for field, item in value.items():
                matches = []
                if field in schema.get("properties", {}):
                    matches.append(schema["properties"][field])
                matches += [child for pattern, child in schema.get("patternProperties", {}).items()
                            if re.search(pattern, field)]
                if not matches and "additionalProperties" in schema:
                    matches.append(schema["additionalProperties"])
                for child in matches:
                    errors += self._errors(item, child, base, location + "/" + field)
        if isinstance(value, list):
            if len(value) < schema.get("minItems", 0):
                fail("MIN_ITEMS", "Array has too few items")
            if len(value) > schema.get("maxItems", len(value)):
                fail("MAX_ITEMS", "Array has too many items")
            if schema.get("uniqueItems") and len({canonical_json(item) for item in value}) != len(value):
                fail("UNIQUE", "Array contains duplicate items")
            if "items" in schema:
                for index, item in enumerate(value):
                    errors += self._errors(item, schema["items"], base, f"{location}/{index}")
        if isinstance(value, str):
            if len(value) < schema.get("minLength", 0):
                fail("MIN_LENGTH", "String is too short")
            if len(value) > schema.get("maxLength", len(value)):
                fail("MAX_LENGTH", "String is too long")
            if "pattern" in schema and not re.search(schema["pattern"], value):
                fail("PATTERN", "String does not match the required format")
            kind = schema.get("format")
            try:
                if kind == "date" and (not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)
                                       or date.fromisoformat(value).isoformat() != value):
                    raise ValueError()
                if kind == "date-time":
                    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    if not re.match(r"\d{4}-\d{2}-\d{2}T", value) or parsed.tzinfo is None:
                        raise ValueError()
                if kind == "uri" and (not urlparse(value).scheme or any(c.isspace() for c in value)):
                    raise ValueError()
            except ValueError:
                fail("FORMAT", "String is not a valid " + str(kind))
        if types["number"]:
            if "minimum" in schema and value < schema["minimum"]:
                fail("MINIMUM", "Number is below its minimum")
            if "maximum" in schema and value > schema["maximum"]:
                fail("MAXIMUM", "Number exceeds its maximum")
        return errors
