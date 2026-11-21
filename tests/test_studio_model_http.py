"""Verify the Studio model HTTP adapters with fully synthetic responses."""

from collections import deque
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import sys
from threading import Thread
from time import monotonic, sleep
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.studio_model_http import (  # noqa: E402
    GeminiProvider,
    OllamaProvider,
    _JsonEndpoint,
)
from mindgarden.domain.validation import ContractError  # noqa: E402


GEMINI_MODEL = "models/gemini-fixture"
LOCAL_MODEL = "gemma3:1b"
PROMPT = "Fictional Willow sample, with no source documents."
API_KEY = "synthetic-test-key"


class FixtureEndpoint:
    def __init__(self, *responses):
        self.responses = deque(responses)
        self.requests = []

    def request(self, path, **arguments):
        self.requests.append((path, arguments))
        return self.responses.popleft()


def gemini_answer(*parts, finish="STOP"):
    return {"candidates": [{"content": {"parts": list(parts)}, "finishReason": finish}]}


def ollama_answer(**message):
    return {
        "done": True,
        "done_reason": "stop",
        "message": {"role": "assistant", "content": "Fictional answer.", **message},
    }


class GeminiAdapterTests(unittest.TestCase):
    def test_missing_explicit_gemini_key_does_not_use_other_credentials(self):
        endpoint = FixtureEndpoint()
        with patch.dict(os.environ, {"GOOGLE_API_KEY": API_KEY}, clear=True):
            provider = GeminiProvider(endpoint=endpoint)
        self.assertEqual(provider.check()["status"], "unconfigured")
        with self.assertRaisesRegex(ContractError, "^MODEL_NOT_CONFIGURED"):
            provider.run(GEMINI_MODEL, PROMPT)
        self.assertEqual(endpoint.requests, [])

    def test_paginates_stable_inventory_and_only_lists_generation_resources(self):
        token = "page&next=yes"
        endpoint = FixtureEndpoint(
            {
                "nextPageToken": token,
                "models": [
                    {
                        "name": "models/embedding",
                        "supportedGenerationMethods": ["embedContent"],
                    },
                    {
                        "name": "tunedModels/user-data",
                        "supportedGenerationMethods": ["generateContent"],
                    },
                    {
                        "name": "models/path/injection",
                        "supportedGenerationMethods": ["generateContent"],
                    },
                ],
            },
            {
                "models": [
                    {
                        "name": GEMINI_MODEL,
                        "displayName": "Fixture",
                        "supportedGenerationMethods": ["generateContent"],
                    },
                ],
            },
        )
        provider = GeminiProvider(api_key=API_KEY, endpoint=endpoint)
        self.assertEqual(
            provider.check()["models"], [{"id": GEMINI_MODEL, "label": "Fixture"}]
        )
        self.assertEqual(
            [path for path, _ in endpoint.requests],
            [
                "/v1/models?pageSize=100",
                "/v1/models?pageSize=100&pageToken=page%26next%3Dyes",
            ],
        )
        for _, request in endpoint.requests:
            self.assertEqual(request["api_key"], API_KEY)
            self.assertNotIn("payload", request)

    def test_repeated_next_page_is_incomplete(self):
        endpoint = FixtureEndpoint(*[{"nextPageToken": "dup"}] * 2)
        provider = GeminiProvider(api_key=API_KEY, endpoint=endpoint)
        self.assertEqual(provider.check()["status"], "unavailable")
        self.assertEqual(len(endpoint.requests), 2)

    def test_sends_only_reviewed_text_and_reads_answer_without_thoughts(self):
        endpoint = FixtureEndpoint(
            gemini_answer(
                {"thought": True, "text": "hidden"},
                {"text": "Fictional "},
                {"text": "answer."},
            )
        )
        provider = GeminiProvider(api_key=API_KEY, endpoint=endpoint)
        self.assertEqual(provider.run(GEMINI_MODEL, PROMPT), "Fictional answer.")
        path, request = endpoint.requests[0]
        self.assertEqual(path, "/v1/" + GEMINI_MODEL + ":generateContent")
        payload = request["payload"]
        self.assertIs(payload["store"], False)
        self.assertNotIn("tools", payload)
        self.assertNotIn("toolConfig", payload)
        self.assertNotIn("systemInstruction", payload)
        self.assertEqual(
            payload["contents"], [{"role": "user", "parts": [{"text": PROMPT}]}]
        )
        self.assertEqual(payload["generationConfig"]["responseModalities"], ["TEXT"])

    def test_rejects_both_tool_shapes_truncation_and_invalid_resource(self):
        for response in (
            gemini_answer({"text": "partial"}, {"functionCall": {"name": "tool"}}),
            gemini_answer({"text": "partial"}, {"toolCall": {}}),
            gemini_answer({"text": "partial"}, finish="MAX_TOKENS"),
            {"promptFeedback": {"blockReason": "SAFETY"}, "candidates": []},
        ):
            with self.subTest(response=response):
                provider = GeminiProvider(
                    api_key=API_KEY, endpoint=FixtureEndpoint(response)
                )
                with self.assertRaisesRegex(ContractError, "^MODEL_UNAVAILABLE"):
                    provider.run(GEMINI_MODEL, PROMPT)
        endpoint = FixtureEndpoint()
        provider = GeminiProvider(api_key=API_KEY, endpoint=endpoint)
        with self.assertRaisesRegex(ContractError, "^MODEL_UNAVAILABLE"):
            provider.run("models/gemini?host=redirect.example", PROMPT)
        self.assertEqual(endpoint.requests, [])


class OllamaAdapterTests(unittest.TestCase):
    def test_inventory_excludes_remote_aliases_and_offers_explicit_downloads(self):
        endpoint = FixtureEndpoint(
            {
                "models": [
                    {"name": LOCAL_MODEL, "model": LOCAL_MODEL},
                    {
                        "name": "apparently-local:latest",
                        "remote_model": "a-cloud-model",
                    },
                    {"name": "other:latest", "remote_host": "https://ollama.com"},
                    {"name": "gpt-oss:120b-cloud"},
                    {"name": "cloud:model"},
                    {"name": "ambiguous", "model": "other-tag"},
                    {"name": "registry.example.local/library/other"},
                ]
            }
        )
        provider = OllamaProvider(endpoint=endpoint)
        result = provider.check()
        self.assertTrue(result["can_run"])
        self.assertEqual(result["models"], [{"id": LOCAL_MODEL, "label": LOCAL_MODEL}])
        self.assertEqual(
            [item["id"] for item in result["downloadable"]], ["gemma4:e2b"]
        )
        self.assertEqual([path for path, _ in endpoint.requests], ["/api/tags"])

    def test_run_rechecks_inventory_and_uses_tool_free_loopback_request(self):
        endpoint = FixtureEndpoint(
            {"models": [{"name": LOCAL_MODEL}]}, ollama_answer(thinking="hidden")
        )
        provider = OllamaProvider(endpoint=endpoint)
        self.assertEqual(provider.run(LOCAL_MODEL, PROMPT), "Fictional answer.")
        self.assertEqual(
            [path for path, _ in endpoint.requests], ["/api/tags", "/api/chat"]
        )
        request = endpoint.requests[1][1]
        self.assertNotIn("api_key", request)
        payload = request["payload"]
        self.assertEqual(payload["messages"], [{"role": "user", "content": PROMPT}])
        self.assertIs(payload["stream"], False)
        self.assertNotIn("tools", payload)
        self.assertLessEqual(payload["options"]["num_predict"], 1024)

    def test_removed_model_and_tool_call_never_produce_answer(self):
        endpoint = FixtureEndpoint(
            {"models": [{"name": LOCAL_MODEL, "remote_model": "hosted"}]}
        )
        provider = OllamaProvider(endpoint=endpoint)
        with self.assertRaisesRegex(ContractError, "^MODEL_UNAVAILABLE"):
            provider.run(LOCAL_MODEL, PROMPT)
        self.assertEqual([path for path, _ in endpoint.requests], ["/api/tags"])
        provider = OllamaProvider(
            endpoint=FixtureEndpoint(
                {"models": [{"name": LOCAL_MODEL}]},
                ollama_answer(tool_calls=[{"name": "danger"}]),
            )
        )
        with self.assertRaisesRegex(ContractError, "^MODEL_UNAVAILABLE"):
            provider.run(LOCAL_MODEL, PROMPT)

    def test_install_posts_only_supported_exact_tags_and_requires_success(self):
        endpoint = FixtureEndpoint(
            {"status": "success"}, {"status": "pulling manifest"}
        )
        provider = OllamaProvider(endpoint=endpoint)
        with self.assertRaisesRegex(ContractError, "^MODEL_UNAVAILABLE"):
            provider.install("untrusted-registry.example/anything:latest")
        self.assertEqual(endpoint.requests, [])
        self.assertIsNone(provider.install(LOCAL_MODEL))
        path, request = endpoint.requests[0]
        self.assertEqual(path, "/api/pull")
        self.assertEqual(
            request["payload"],
            {"model": LOCAL_MODEL, "stream": False, "insecure": False},
        )
        self.assertLessEqual(request["seconds"], 300)
        with self.assertRaisesRegex(ContractError, "^MODEL_UNAVAILABLE"):
            provider.install("gemma4:e2b")


class JsonEndpointTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        requests = self.requests

        class LocalProvider(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append((self.path, self.headers.get("x-goog-api-key")))
                if self.path == "/drip":
                    self.drip_incomplete_header()
                    return
                response = {
                    "/redirect": (307, b'{"error":"private redirect failure"}'),
                    "/quota": (429, b'{"error":"private quota failure"}'),
                    "/body-limit": (200, b'{"models":["a","b","c"]}'),
                    "/ok": (200, b'{"models":[]}'),
                    "/close-length": (200, b'{"models":[]}'),
                    "/close-short": (200, b'{"models":[]}'),
                }
                status, body = response[self.path]
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                if self.path in {"/close-length", "/close-short"}:
                    adjustment = int(self.path == "/close-short")
                    self.send_header("Content-Length", str(len(body) + adjustment))
                    self.send_header("Connection", "close")
                if self.path == "/redirect":
                    self.send_header("Location", "/ok")
                self.end_headers()
                self.wfile.write(body)

            def drip_incomplete_header(self):
                try:
                    self.wfile.write(
                        b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nX-Drip: "
                    )
                    for _ in range(40):
                        self.wfile.write(b"x")
                        sleep(0.05)
                except OSError:
                    pass

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), LocalProvider)
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(worker.join, 2)
        self.addCleanup(server.shutdown)
        self.endpoint = _JsonEndpoint("127.0.0.1", server.server_port, HTTPConnection)

    def test_direct_client_refuses_redirect_and_ignores_proxy_environment(self):
        with patch.dict(
            os.environ,
            {
                "HTTP_PROXY": "http://127.0.0.1:1",
                "HTTPS_PROXY": "http://127.0.0.1:1",
                "NO_PROXY": "",
            },
        ):
            with self.assertRaisesRegex(ContractError, "^MODEL_UNAVAILABLE") as failure:
                self.endpoint.request(
                    "/redirect", api_key=API_KEY, seconds=2, limit=100
                )
            self.assertEqual(self.requests, [("/redirect", API_KEY)])
            self.assertNotIn(API_KEY, str(failure.exception))
            self.assertNotIn("private redirect failure", str(failure.exception))
            self.assertEqual(
                self.endpoint.request("/ok", seconds=2, limit=100), {"models": []}
            )

    def test_body_limit_without_content_length_and_quota_are_sanitized(self):
        with self.assertRaisesRegex(ContractError, "^MODEL_UNAVAILABLE"):
            self.endpoint.request("/body-limit", seconds=2, limit=10)
        with self.assertRaisesRegex(ContractError, "^MODEL_QUOTA") as failure:
            self.endpoint.request("/quota", seconds=2, limit=100)
        self.assertNotIn("private quota failure", str(failure.exception))

    def test_sockets_have_an_overall_deadline_when_headers_drip(self):
        started = monotonic()
        with self.assertRaisesRegex(ContractError, "^MODEL_UNAVAILABLE"):
            self.endpoint.request("/drip", seconds=0.3, limit=100)
        self.assertLess(monotonic() - started, 1.5)

    def test_reads_content_length_when_connection_closes_and_rejects_short_body(self):
        self.assertEqual(
            self.endpoint.request("/close-length", seconds=2, limit=100), {"models": []}
        )
        with self.assertRaisesRegex(ContractError, "^MODEL_UNAVAILABLE.*incomplete"):
            self.endpoint.request("/close-short", seconds=2, limit=100)
