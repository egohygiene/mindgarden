#!/usr/bin/env python3
"""Optional local-model probe using committed synthetic text only; dry-run default."""

from argparse import ArgumentParser
from pathlib import Path
import sys
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from mindgarden.adapters.ollama_extraction import chat_request, parse_reply
from mindgarden.application.extraction import validate_output
from mindgarden.domain.contracts import canonical_json, digest_bytes, strict_json
from mindgarden.domain.validation import ContractError


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def evaluate(model, endpoint, live, *, include_output=False, timeout=30):
    if not 1 <= timeout <= 120:
        raise ValueError("Select a timeout between 1 and 120 seconds")
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Select an explicit loopback-only Ollama endpoint")
    text = (
        Path(__file__).resolve().parents[2] / "tests/fixtures/extraction/page.txt"
    ).read_text()
    descriptor = {"model": model}
    payload = chat_request(
        {"text": text, "trust": "untrusted-synthetic-source"}, descriptor
    )
    report = {
        "schema": "mindgarden.ollama-extraction-evaluation/v1",
        "model_requested": model,
        "request_sha256": digest_bytes(canonical_json(payload)),
        "mode": "live" if live else "dry-run",
        "cases": 1,
        "model_accuracy": None,
        "accuracy_status": "unmeasured",
        "expected_review_cases": [
            "ambiguous Alex",
            "positive/negative accuracy reports",
            "exact quotations",
        ],
        "core_network_policy": "unchanged; private source grants are offline",
    }
    if live:
        opener = build_opener(ProxyHandler({}), NoRedirect())
        request = Request(
            endpoint.rstrip("/") + "/api/chat",
            data=canonical_json(payload),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with opener.open(request, timeout=timeout) as response:
                content = response.read(262145)
        except TimeoutError:
            return {**report, "structure": "unavailable", "validation_code": "OLLAMA_TIMEOUT"}
        except OSError:
            return {**report, "structure": "unavailable", "validation_code": "OLLAMA_UNAVAILABLE"}
        if len(content) > 262144:
            return {**report, "structure": "rejected", "validation_code": "OLLAMA_RESPONSE_LIMIT"}
        try:
            observed = parse_reply(strict_json(content))
        except ContractError:
            return {**report, "structure": "rejected", "validation_code": "OLLAMA_REPLY"}
        output = observed["output"]
        report.update(
            model_used=observed["model_used"],
            structure="passed",
            output_sha256=digest_bytes(canonical_json(output)),
            interpretation="requires authored comparison and explicit human review",
        )
        if include_output:
            report["output"] = output
        try:
            validate_output(output, text, 262144)
        except ContractError as error:
            report.update(proposal_validation="rejected", validation_diagnostic=str(error))
        else:
            report["proposal_validation"] = "passed"
    return report


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        required=True,
        help="Explicit locally installed model identifier; record the actual response model",
    )
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicitly contact the selected local model with committed synthetic input",
    )
    parser.add_argument(
        "--include-output",
        action="store_true",
        help="Include the model's proposal for the committed synthetic input in the report",
    )
    parser.add_argument("--timeout-seconds", default=30, type=int, help="HTTP timeout from 1 to 120 seconds")
    arguments = parser.parse_args()
    if not 1 <= arguments.timeout_seconds <= 120:
        parser.error("--timeout-seconds must be from 1 to 120")
    report = evaluate(
        arguments.model, arguments.endpoint, arguments.live, include_output=arguments.include_output,
        timeout=arguments.timeout_seconds,
    )
    print(canonical_json(report).decode(), end="")
    if arguments.live and report.get("proposal_validation") != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
