"""Public token/schema conformance and deterministic, accessible consumers."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from jsonschema import Draft202012Validator
from mindgarden.application.site import build_site
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.design import contrast, css_variables, design_directory, load_tokens, quartz_styles, quartz_theme, validate_tokens
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.cli import main
from tests.site_fixture import create_fixture


class DesignTests(unittest.TestCase):
    def test_source_schema_and_semantic_color_pairs_are_accessible(self):
        tokens = load_tokens()
        schema = json.loads((design_directory() / "schemas/design-tokens.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(tokens)), [])
        for mode, colors in tokens["colors"].items():
            for surface in ("background", "surface"):
                for role in ("text", "muted", "accent"):
                    with self.subTest(mode=mode, surface=surface, role=role):
                        self.assertGreaterEqual(contrast(colors[role], colors[surface]), 4.5)
                self.assertGreaterEqual(contrast(colors["focus"], colors[surface]), 3)

    def test_unknown_tokens_font_injection_and_low_contrast_fail_closed(self):
        original = load_tokens()
        cases = []
        tokens = deepcopy(original); tokens["network"] = "https://unexpected.example.test"; cases.append((tokens, "DESIGN_TOKENS"))
        tokens = deepcopy(original); tokens["typography"]["body_family"] = ['x; background:url(https://unexpected.example.test)']; cases.append((tokens, "DESIGN_TOKENS"))
        tokens = deepcopy(original); tokens["colors"]["dark"]["text"] = tokens["colors"]["dark"]["background"]; cases.append((tokens, "DESIGN_CONTRAST"))
        for tokens, code in cases:
            with self.subTest(code=code), self.assertRaisesRegex(ContractError, code):
                validate_tokens(tokens)

    def test_cli_exports_validated_stack_neutral_css_and_quartz_views(self):
        tokens = load_tokens()
        for format in ("json", "css", "quartz"):
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["design", "--format", format]), 0)
            if format == "css":
                self.assertEqual(output.getvalue(), css_variables(tokens))
                self.assertNotIn("http", output.getvalue())
            else:
                self.assertEqual(json.loads(output.getvalue()), tokens if format == "json" else quartz_theme(tokens))

    def test_site_theme_is_optional_revision_bound_and_does_not_change_canonical_records(self):
        with TemporaryDirectory() as temporary:
            fixture = create_fixture(Path(temporary))
            plain = build_site(fixture["context"], fixture["profile"])
            self.assertNotIn("static/mindgarden/theme.css", plain.files)
            profile = deepcopy(fixture["profile"]); profile["x-site"]["theme"] = "mindgarden-v1"
            themed = build_site(fixture["context"], profile)
            expected = "sha256:" + digest_bytes(canonical_json(load_tokens()))
            self.assertEqual(themed.settings["theme_revision"], expected)
            self.assertEqual(themed.files["static/mindgarden/theme.css"], quartz_styles(load_tokens()).encode())
            self.assertNotEqual(themed.manifest["revision"], plain.manifest["revision"])
            profile["x-site"]["theme_revision"] = "sha256:" + "0" * 64
            with self.assertRaisesRegex(ContractError, "DESIGN_STALE"):
                build_site(fixture["context"], profile)
