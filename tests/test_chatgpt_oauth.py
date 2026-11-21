"""Fixture-only OAuth exchanges with locally signed OIDC tokens."""

from base64 import urlsafe_b64encode
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
import sys
from time import monotonic, time
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from mindgarden.adapters import chatgpt_oauth as oauth
from mindgarden.domain.validation import ContractError

try:
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
except ImportError:
    jwt = rsa = None


HOST_ID = "urn:uuid:90d75ce7-d228-4c32-a0e5-997afd108d17"
CALLBACK = "http://127.0.0.1:1455/auth/callback"
CLIENT_ID = "oaiapp_fictional"
SUBJECT = "user-fictional"


class AttemptTests(unittest.TestCase):
    def test_optional_verification_dependency_required_before_an_exchange(self):
        with patch.dict(sys.modules, {"jwt": None}):
            with self.assertRaisesRegex(ContractError, "^CHATGPT_OAUTH_DEPENDENCY"):
                oauth.OAuthClient.require_oidc()

    def test_local_dynamic_registration_and_reauthorization(self):
        initial = oauth.new_attempt(HOST_ID, CALLBACK)
        first_url = urlsplit(initial.authorization_url)
        first = parse_qs(first_url.query)
        self.assertEqual(
            (first_url.scheme, first_url.netloc, first_url.path),
            ("https", "auth.openai.com", oauth.AUTHORIZE_PATH),
        )
        self.assertEqual(first["scope"], [" ".join(oauth.SCOPES)])
        self.assertEqual(first["client_id"], ["dynamic_agent_client"])
        self.assertEqual(first["agent_name_hint"], ["Mindgarden Studio"])
        self.assertEqual(first["ext_agent_host_id"], [HOST_ID])
        self.assertEqual(first["redirect_uri"], [CALLBACK])
        self.assertEqual(first["resource"], [oauth.RESOURCE])
        self.assertEqual(first["state"], [initial.state])
        self.assertEqual(first["code_challenge_method"], ["S256"])
        expected = (
            urlsafe_b64encode(sha256(initial._verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        self.assertEqual(first["code_challenge"], [expected])
        self.assertNotIn(initial._verifier, initial.authorization_url)
        self.assertNotIn(initial.state, repr(initial))

        returning = oauth.new_attempt(HOST_ID, CALLBACK, CLIENT_ID)
        later = parse_qs(urlsplit(returning.authorization_url).query)
        self.assertEqual(later["client_id"], [CLIENT_ID])
        self.assertNotIn("agent_name_hint", later)
        for key in ("state", "nonce", "code_challenge"):
            self.assertNotEqual(first[key], later[key])

    def test_only_exact_local_callback_and_opaque_issued_id(self):
        for uri in (
            "http://localhost:1455/auth/callback",
            "https://127.0.0.1:1455/auth/callback",
            "http://127.0.0.1:1455/auth/callback?code=private-canary",
            "http://127.0.0.1:65536/auth/callback",
            "http://127.0.0.1:01455/auth/callback",
            "http://127.0.0.1:1455/callback",
        ):
            with (
                self.subTest(uri=uri),
                self.assertRaisesRegex(ContractError, "^CHATGPT_OAUTH_ATTEMPT"),
            ):
                oauth.new_attempt(HOST_ID, uri)
        with self.assertRaisesRegex(ContractError, "^CHATGPT_OAUTH_ATTEMPT"):
            oauth.new_attempt(HOST_ID, CALLBACK, "dynamic_agent_client")


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, path, *, deadline, form=None, empty=False):
        self.calls.append((path, form, empty))
        expected, response = self.responses.pop(0)
        if path != expected or deadline < monotonic():
            raise AssertionError("Unexpected authorization transport request")
        return response


@unittest.skipUnless(jwt and rsa, "Optional PyJWT and cryptography install required")
class VerifiedExchangeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.signer = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.other_signer = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        cls.jwk = json.loads(
            jwt.algorithms.RSAAlgorithm.to_jwk(cls.signer.public_key())
        )
        cls.jwk.update(kid="fixture-rsa", alg="RS256", use="sig")

    def setUp(self):
        self.attempt = oauth.new_attempt(HOST_ID, CALLBACK)
        self.jwks = {"keys": [self.jwk]}

    def token(self, *, signer=None, kid="fixture-rsa", **changes):
        now = int(time())
        claims = {
            "iss": oauth.ISSUER,
            "sub": SUBJECT,
            "aud": CLIENT_ID,
            "iat": now - 5,
            "exp": now + 3600,
            "nonce": self.attempt._nonce,
            "email": "private-canary@example.test",
        }
        claims.update(changes)
        return jwt.encode(
            claims, signer or self.signer, algorithm="RS256", headers={"kid": kid}
        )

    def response(self, **changes):
        result = {
            "access_token": "private-access-canary",
            "refresh_token": "private-renewal-canary",
            "id_token": self.token(),
            "scope": " ".join(oauth.SCOPES),
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        result.update(changes)
        return result

    def exchange(self, value=None, *, jwks=None):
        return oauth.OAuthClient(
            FakeTransport(
                [
                    (oauth.TOKEN_PATH, self.response() if value is None else value),
                    (oauth.JWKS_PATH, self.jwks if jwks is None else jwks),
                ]
            )
        ).exchange(self.attempt, "fictional-code", CLIENT_ID)

    def test_code_exchange_requires_signed_identity_and_exact_grant(self):
        transport = FakeTransport(
            [
                (
                    oauth.TOKEN_PATH,
                    self.response(earliest_refresh_at="2030-01-01T00:00:00Z"),
                ),
                (oauth.JWKS_PATH, self.jwks),
            ]
        )
        with patch.object(oauth, "time", return_value=1_893_456_000):
            result = oauth.OAuthClient(transport).exchange(
                self.attempt, "fictional-code", CLIENT_ID
            )
        self.assertEqual(
            (result.issuer, result.subject, result.client_id),
            (oauth.ISSUER, SUBJECT, CLIENT_ID),
        )
        self.assertEqual(result.scopes, tuple(sorted(oauth.SCOPES)))
        self.assertEqual(result.expires_at, 1_893_459_600)
        self.assertEqual(result.earliest_refresh_at, 1_893_456_000)
        self.assertEqual(
            transport.calls,
            [
                (
                    oauth.TOKEN_PATH,
                    {
                        "grant_type": "authorization_code",
                        "client_id": CLIENT_ID,
                        "code": "fictional-code",
                        "code_verifier": self.attempt._verifier,
                        "redirect_uri": CALLBACK,
                        "resource": oauth.RESOURCE,
                    },
                    False,
                ),
                (oauth.JWKS_PATH, None, False),
            ],
        )

    def test_callback_client_binding_fails_before_transmitting_code(self):
        unbound = FakeTransport([])
        client = oauth.OAuthClient(unbound)
        returning = oauth.new_attempt(HOST_ID, CALLBACK, CLIENT_ID)
        for attempt, issued in (
            (self.attempt, None),
            (self.attempt, "dynamic_agent_client"),
            (self.attempt, "private/canary"),
            (returning, "wrong-client"),
        ):
            with (
                self.subTest(issued=issued),
                self.assertRaisesRegex(ContractError, "^CHATGPT_OAUTH_CALLBACK"),
            ):
                client.exchange(attempt, "private-code-canary", issued)
        self.assertEqual(unbound.calls, [])

        self.attempt = returning
        transport = FakeTransport(
            [(oauth.TOKEN_PATH, self.response()), (oauth.JWKS_PATH, self.jwks)]
        )
        result = oauth.OAuthClient(transport).exchange(
            returning, "fictional-code", None
        )
        self.assertEqual(result.client_id, CLIENT_ID)

    def test_wrong_signature_claims_nonce_and_key_denied_without_raw_data(self):
        cases = (
            self.token(signer=self.other_signer),
            self.token(kid="unknown"),
            self.token(iss="https://private-canary.example"),
            self.token(aud="other-client"),
            self.token(aud=[CLIENT_ID, "other-client"]),
            self.token(aud=[CLIENT_ID, "other-client"], azp=CLIENT_ID),
            self.token(nonce="wrong-nonce"),
            self.token(exp=int(time()) - 10),
            self.token(iat=str(int(time()) - 10)),
            self.token(azp="other-client"),
        )
        for index, token in enumerate(cases):
            with (
                self.subTest(index=index),
                self.assertRaisesRegex(
                    ContractError,
                    "^CHATGPT_OAUTH_IDENTITY: the OpenAI identity could not be verified$",
                ),
            ):
                self.exchange(self.response(id_token=token))
        with self.assertRaisesRegex(ContractError, "^CHATGPT_OAUTH_IDENTITY"):
            self.exchange(jwks={"keys": [self.jwk, self.jwk]})

    def test_denied_narrower_or_unexpected_scope_fails_before_jwks(self):
        for scope in (
            "openid email profile",
            " ".join((*oauth.SCOPES, "unknown")),
            " ".join((*oauth.SCOPES, oauth.SCOPES[0])),
        ):
            with self.subTest(scope=scope):
                transport = FakeTransport(
                    [(oauth.TOKEN_PATH, self.response(scope=scope))]
                )
                with self.assertRaisesRegex(ContractError, "^CHATGPT_OAUTH_SCOPE"):
                    oauth.OAuthClient(transport).exchange(
                        self.attempt, "fixture", CLIENT_ID
                    )
                self.assertEqual(len(transport.calls), 1)

    def test_refresh_rotates_once_and_retains_identity_if_omitted(self):
        previous = self.exchange()
        value = self.response(
            access_token="fixture-new-access",
            refresh_token="fixture-new-renewal",
            earliest_refresh_at="1893456000",
        )
        del value["scope"], value["id_token"]
        transport = FakeTransport([(oauth.TOKEN_PATH, value)])
        updated = oauth.OAuthClient(transport).refresh(previous)
        self.assertEqual(updated.id_token, previous.id_token)
        self.assertEqual(updated.subject, previous.subject)
        self.assertEqual(updated.scopes, previous.scopes)
        self.assertEqual(updated.refresh_token, "fixture-new-renewal")
        self.assertEqual(updated.earliest_refresh_at, 1_893_456_000)
        self.assertEqual(
            transport.calls,
            [
                (
                    oauth.TOKEN_PATH,
                    {
                        "grant_type": "refresh_token",
                        "client_id": CLIENT_ID,
                        "refresh_token": previous.refresh_token,
                        "resource": oauth.RESOURCE,
                    },
                    False,
                )
            ],
        )

    def test_refresh_rejects_reused_refresh_or_different_identity(self):
        previous = self.exchange()
        replay = FakeTransport([(oauth.TOKEN_PATH, self.response())])
        with self.assertRaisesRegex(ContractError, "^CHATGPT_OAUTH_RESPONSE"):
            oauth.OAuthClient(replay).refresh(previous)
        wrong_identity = FakeTransport(
            [
                (
                    oauth.TOKEN_PATH,
                    self.response(
                        refresh_token="replacement", id_token=self.token(sub="other")
                    ),
                ),
                (oauth.JWKS_PATH, self.jwks),
            ]
        )
        with self.assertRaisesRegex(ContractError, "^CHATGPT_OAUTH_IDENTITY"):
            oauth.OAuthClient(wrong_identity).refresh(previous)
        self.assertEqual(len(wrong_identity.calls), 2)

    def test_revocation_follows_only_exact_verified_openai_endpoint(self):
        previous = self.exchange()
        denied = FakeTransport(
            [
                (
                    oauth.DISCOVERY_PATH,
                    {
                        "issuer": oauth.ISSUER,
                        "revocation_endpoint": "https://private-canary.example/revoke",
                    },
                )
            ]
        )
        with self.assertRaisesRegex(
            ContractError,
            "^CHATGPT_OAUTH_REVOCATION: remote disconnection was not confirmed$",
        ):
            oauth.OAuthClient(denied).revoke(previous)
        self.assertEqual(denied.calls, [(oauth.DISCOVERY_PATH, None, False)])

        allowed = FakeTransport(
            [
                (
                    oauth.DISCOVERY_PATH,
                    {
                        "issuer": oauth.ISSUER,
                        "revocation_endpoint": oauth.ISSUER + oauth.REVOKE_PATH,
                    },
                ),
                (oauth.REVOKE_PATH, None),
            ]
        )
        self.assertIsNone(oauth.OAuthClient(allowed).revoke(previous))
        self.assertEqual(
            allowed.calls[-1],
            (
                oauth.REVOKE_PATH,
                {
                    "token": previous.refresh_token,
                    "token_type_hint": "refresh_token",
                    "client_id": CLIENT_ID,
                },
                True,
            ),
        )
        with self.assertRaisesRegex(ContractError, "^CHATGPT_OAUTH_IDENTITY"):
            oauth.OAuthClient(FakeTransport([])).revoke(
                replace(previous, issuer="https://wrong.example")
            )


class TransportTests(unittest.TestCase):
    def test_only_known_bounded_refresh_refusals_require_reauthorization(self):
        class Response(BytesIO):
            def __init__(self, status, body):
                super().__init__(body)
                self.status = status
                self.length = len(body)

            def getheader(self, name, default=None):
                return {
                    "Content-Type": "application/json",
                    "Content-Length": str(self.length),
                }.get(name, default)

        secret = "private-response-canary"
        known_codes = (
            "invalid_grant",
            "invalid_refresh_token",
            "token_expired",
            "refresh_token_expired",
            "refresh_token_invalidated",
            "refresh_token_reused",
        )
        cases = [
            (status, "refresh_token", {"error": error}, "REFRESH_REAUTHORIZE")
            for code in known_codes
            for status, error in ((400, code), (401, {"code": code, "message": secret}))
        ]
        cases.extend(
            (
                (
                    403,
                    "refresh_token",
                    {"error": "invalid_grant"},
                    "REFRESH_REAUTHORIZE",
                ),
                (400, "authorization_code", {"error": "invalid_grant"}, "OAUTH_DENIED"),
                (400, "refresh_token", {"error": "invalid_client"}, "OAUTH_CLIENT"),
                (
                    400,
                    "refresh_token",
                    {"error": "temporarily_unavailable"},
                    "OAUTH_DENIED",
                ),
                (429, "refresh_token", {"error": "invalid_grant"}, "OAUTH_UNAVAILABLE"),
                (503, "refresh_token", {"error": "invalid_grant"}, "OAUTH_UNAVAILABLE"),
                (
                    400,
                    "refresh_token",
                    {"error_description": "invalid_grant"},
                    "OAUTH_DENIED",
                ),
                (
                    400,
                    "refresh_token",
                    {"error": {"message": "invalid_grant"}},
                    "OAUTH_DENIED",
                ),
                (
                    400,
                    "refresh_token",
                    {"error": "invalid_grant", "secret": secret * 1000},
                    "OAUTH_DENIED",
                ),
                (400, "refresh_token", b'{"error":"invalid_grant"', "OAUTH_DENIED"),
                (
                    400,
                    "refresh_token",
                    b'{"error":"unknown","error":"invalid_grant"}',
                    "OAUTH_DENIED",
                ),
            )
        )
        for status, grant_type, value, diagnostic in cases:
            with self.subTest(
                status=status, grant_type=grant_type, diagnostic=diagnostic
            ):
                body = value if isinstance(value, bytes) else json.dumps(value).encode()
                with patch.object(oauth, "HTTPSConnection") as connect:
                    connect.return_value.getresponse.return_value = Response(
                        status, body
                    )
                    with self.assertRaisesRegex(
                        ContractError, f"^CHATGPT_{diagnostic}:"
                    ) as caught:
                        oauth._OpenAITransport().request(
                            oauth.TOKEN_PATH,
                            deadline=monotonic() + 4,
                            form={"grant_type": grant_type},
                        )
                self.assertNotIn(secret, str(caught.exception))

    def test_response_rejects_large_truncated_and_nonempty_revocation_bodies(self):
        class Socket:
            def settimeout(self, timeout):
                pass

        class Response(BytesIO):
            def __init__(self, body, length=None, encoding="identity"):
                super().__init__(body)
                self.headers = {
                    "Content-Type": "application/json",
                    "Content-Encoding": encoding,
                }
                if length is not None:
                    self.headers["Content-Length"] = str(length)

            def getheader(self, name, default=None):
                return self.headers.get(name, default)

        for response, empty, diagnostic in (
            (Response(b"{}", oauth.RESPONSE_LIMIT + 1), False, "LIMIT"),
            (Response(b"x" * (oauth.RESPONSE_LIMIT + 1)), False, "LIMIT"),
            (Response(b"{}", 9), False, "LIMIT"),
            (Response(b"{}", encoding="gzip"), False, "RESPONSE"),
            (Response(b"{}", 2), True, "LIMIT"),
        ):
            with self.subTest(empty=empty, diagnostic=diagnostic):
                with self.assertRaisesRegex(
                    ContractError, "^CHATGPT_OAUTH_" + diagnostic
                ):
                    oauth._response_body(
                        response, Socket(), monotonic() + 4, empty=empty
                    )
        self.assertEqual(
            oauth._response_body(
                Response(b"", 0), Socket(), monotonic() + 4, empty=True
            ),
            b"",
        )

    def test_enforces_fixed_host_method_form_and_no_redirect(self):
        class Socket:
            def settimeout(self, timeout):
                pass

        class Response(BytesIO):
            status = 302

        recorded = []

        class Connection:
            sock = Socket()

            def __init__(self, host, port, *, timeout):
                recorded.append((host, port))

            def connect(self):
                pass

            def request(self, method, path, body, headers):
                recorded.append(
                    (method, path, parse_qs(body.decode()), headers["Content-Type"])
                )

            def getresponse(self):
                return Response()

            def close(self):
                pass

        with patch.object(oauth, "HTTPSConnection", Connection):
            transport = oauth._OpenAITransport()
            with self.assertRaisesRegex(ContractError, "^CHATGPT_OAUTH_UNAVAILABLE"):
                transport.request(
                    oauth.TOKEN_PATH, deadline=monotonic() + 4, form={"code": "a+%b"}
                )
            with self.assertRaisesRegex(ContractError, "^CHATGPT_OAUTH_ENDPOINT"):
                transport.request(
                    "https://other.example/?code=private-canary",
                    deadline=monotonic() + 4,
                )
        self.assertEqual(
            recorded,
            [
                ("auth.openai.com", 443),
                (
                    "POST",
                    oauth.TOKEN_PATH,
                    {"code": ["a+%b"]},
                    "application/x-www-form-urlencoded",
                ),
            ],
        )
