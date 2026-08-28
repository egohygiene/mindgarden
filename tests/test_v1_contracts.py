# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
except ModuleNotFoundError:  # pragma: no cover - exercised without test extras
    Draft202012Validator = None  # type: ignore[assignment,misc]
    FormatChecker = None  # type: ignore[assignment,misc]
    Registry = None  # type: ignore[assignment,misc]
    Resource = None  # type: ignore[assignment,misc]

MINDGARDEN_ROOT = Path(__file__).parents[1]
CONTRACT_ROOT = MINDGARDEN_ROOT / "contracts/v1"
FIXTURE_ROOT = MINDGARDEN_ROOT / "tests/fixtures/contracts/v1"
VALID_ROOT = FIXTURE_ROOT / "valid"
INVALID_CASES = FIXTURE_ROOT / "invalid/cases.json"


def load_json(path: Path) -> dict[str, object]:
    """Load one UTF-8 JSON object."""
    value = json.loads(path.read_text(encoding="utf8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return value


def decode_pointer_token(token: str) -> str:
    """Decode one RFC 6901 JSON Pointer token."""
    return token.replace("~1", "/").replace("~0", "~")


def apply_mutation(instance: dict[str, object], mutation: dict[str, object]) -> None:
    """Apply the fixture subset of JSON Patch operations."""
    pointer = mutation["pointer"]
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError(f"invalid fixture pointer: {pointer!r}")
    tokens = [decode_pointer_token(token) for token in pointer[1:].split("/")]
    parent: object = instance
    for token in tokens[:-1]:
        if isinstance(parent, dict):
            parent = parent[token]
        elif isinstance(parent, list):
            parent = parent[int(token)]
        else:
            raise TypeError(f"fixture pointer crosses a scalar: {pointer}")

    operation = mutation["operation"]
    final = tokens[-1]
    if operation == "remove":
        if isinstance(parent, dict):
            del parent[final]
        elif isinstance(parent, list):
            del parent[int(final)]
        else:
            raise TypeError(f"fixture remove targets a scalar: {pointer}")
        return

    value = deepcopy(mutation["value"])
    if isinstance(parent, dict):
        if operation == "replace" and final not in parent:
            raise KeyError(f"fixture replace target does not exist: {pointer}")
        parent[final] = value
    elif isinstance(parent, list):
        if operation == "add" and final == "-":
            parent.append(value)
        else:
            parent[int(final)] = value
    else:
        raise TypeError(f"fixture mutation targets a scalar: {pointer}")


@unittest.skipUnless(Draft202012Validator, "install requirements/test.txt")
class V1ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {
            path.stem.removesuffix(".schema"): load_json(path)
            for path in sorted(CONTRACT_ROOT.glob("*.schema.json"))
        }
        resources = [
            (str(schema["$id"]), Resource.from_contents(schema))
            for schema in cls.schemas.values()
        ]
        cls.registry = Registry().with_resources(resources)

    def validator(self, contract: str) -> Draft202012Validator:
        """Build a v1 validator with the complete local contract registry."""
        return Draft202012Validator(
            self.schemas[contract],
            registry=self.registry,
            format_checker=FormatChecker(),
        )

    def test_schema_registry_is_valid_draft_2020_12(self) -> None:
        self.assertEqual(
            set(self.schemas),
            {
                "claim",
                "common",
                "garden",
                "knowledge",
                "migration",
                "projection",
                "provenance",
                "source",
                "synapse",
            },
        )
        identifiers = set()
        for schema in self.schemas.values():
            Draft202012Validator.check_schema(schema)
            self.assertEqual(
                schema["$schema"],
                "https://json-schema.org/draft/2020-12/schema",
            )
            identifiers.add(schema["$id"])
        self.assertEqual(len(identifiers), len(self.schemas))

    def test_all_valid_contract_fixtures_conform(self) -> None:
        for fixture_path in sorted(VALID_ROOT.glob("*.json")):
            with self.subTest(fixture=fixture_path.name):
                instance = load_json(fixture_path)
                contract = (
                    str(instance["schema"])
                    .removeprefix("mindgarden.")
                    .split("/")[0]
                )
                self.validator(contract).validate(instance)

    def test_adversarial_mutations_fail_for_the_expected_reason(self) -> None:
        fixture_matrix = load_json(INVALID_CASES)
        cases = fixture_matrix["cases"]
        self.assertIsInstance(cases, list)
        categories = set()
        for case in cases:
            self.assertIsInstance(case, dict)
            categories.add(case["category"])
            instance = load_json(VALID_ROOT / str(case["base"]))
            for mutation in case["mutations"]:
                apply_mutation(instance, mutation)
            errors = list(self.validator(str(case["contract"])).iter_errors(instance))
            validators = {error.validator for error in errors}
            with self.subTest(case=case["id"]):
                self.assertTrue(errors, "adversarial fixture unexpectedly validated")
                self.assertIn(case["expected_validator"], validators)

        self.assertEqual(
            categories,
            {
                "claim-evidence",
                "classification",
                "cross-garden-reference",
                "dates",
                "extension-fields",
                "garden-identity",
                "identity",
                "migration-history",
                "origin",
                "privacy",
                "provenance",
                "publication-policy",
                "relationships",
                "review-authority",
            },
        )

    def test_private_and_agent_defaults_are_explicit_in_contracts(self) -> None:
        common_definitions = self.schemas["common"]["$defs"]
        source_properties = self.schemas["source"]["properties"]
        knowledge_properties = self.schemas["knowledge"]["properties"]
        self.assertEqual(
            common_definitions["review"]["properties"]["state"]["default"],
            "unreviewed",
        )
        self.assertEqual(source_properties["visibility"]["default"], "private")
        self.assertEqual(source_properties["publication"]["default"], "excluded")
        self.assertEqual(knowledge_properties["status"]["default"], "proposed")
        self.assertEqual(knowledge_properties["visibility"]["default"], "private")
        self.assertEqual(knowledge_properties["publication"]["default"], "excluded")

    def test_ontology_and_claim_schema_share_the_v1_vocabulary(self) -> None:
        ontology = (MINDGARDEN_ROOT / "ONTOLOGY.md").read_text(encoding="utf8")
        for concept in (
            "Garden",
            "Source",
            "Knowledge",
            "Claim",
            "Synapse",
            "Provenance",
            "Projection",
            "Migration record",
        ):
            self.assertIn(f"| {concept} |", ontology)

        relationships = self.schemas["claim"]["properties"]["evidence"]["items"][
            "properties"
        ]["relationship"]["enum"]
        self.assertEqual(
            set(relationships),
            {"supports", "contradicts", "uncertain", "supersedes"},
        )


if __name__ == "__main__":
    unittest.main()
