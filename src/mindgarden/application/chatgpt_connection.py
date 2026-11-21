"""Orchestrate explicit local ChatGPT consent and its owner-side lifecycle."""

from contextlib import nullcontext
from pathlib import Path
from time import time

from ..adapters.chatgpt_credentials import ChatGPTStore
from ..adapters.chatgpt_oauth import OAuthClient, new_attempt
from ..domain.validation import ContractError


def status(directory: Path, *, clock=time) -> dict:
    """Read cached availability without opening the browser or contacting OpenAI."""
    store = ChatGPTStore(directory)
    credentials = store.read()
    if credentials is None:
        return {"status": "signed-out", "registration_saved": store.registration() is not None}
    return {
        "status": "ready" if credentials.expires_at > int(clock()) + 30 else "expired",
        "registration_saved": True,
        "expires_at": credentials.expires_at,
    }


def connect(directory: Path, *, callback, browse, oauth=None, guard=lambda: None,
            on_callback=lambda: None, committing=nullcontext) -> dict:
    """Open a one-use browser authorization and save only verified consent."""
    guard()
    client = OAuthClient() if oauth is None else oauth
    client.require_oidc()
    store = ChatGPTStore(directory)
    with store.writer():
        guard()
        saved = store.registration()
        host = store.host_id()
        with callback() as listener:
            attempt = new_attempt(host, listener.redirect_uri, saved.client_id if saved else None)
            try:
                guard()
                if (arm := getattr(listener, "arm", None)) is not None:
                    arm(attempt.state)
                try:
                    opened = browse(attempt.authorization_url)
                except ContractError:
                    raise
                except (OSError, ValueError):
                    opened = False
                if not opened:
                    raise ContractError("CHATGPT_BROWSER: open this command from a session with a system browser")
                code, client_id = listener.wait(attempt.state)
            except KeyboardInterrupt:
                raise ContractError("CHATGPT_CALLBACK_CANCELLED: local sign-in was cancelled") from None
        guard()
        on_callback()
        credentials = client.exchange(attempt, code, client_id)
        with committing():
            guard()
            store.save(credentials)
    return {"status": "authorized", "registration_saved": True}


def refresh(directory: Path, *, oauth=None, clock=time) -> dict:
    """Refresh the selected registration with its latest rotating credential."""
    store = ChatGPTStore(directory)
    with store.writer():
        current = store.read()
        if current is None:
            raise ContractError("CHATGPT_SIGN_IN: sign in before refreshing the local session")
        earliest = current.earliest_refresh_at
        if earliest is not None and int(clock()) < earliest:
            return {"status": "refresh-not-due", "expires_at": current.expires_at}
        client = OAuthClient() if oauth is None else oauth
        try:
            renewed = client.refresh(current)
        except ContractError as error:
            if str(error).startswith(("CHATGPT_REFRESH_REAUTHORIZE:", "CHATGPT_OAUTH_SCOPE:")):
                store.clear()
            raise
        store.save(renewed)
    return {"status": "refreshed", "expires_at": renewed.expires_at}


def disconnect(directory: Path, *, oauth=None, guard=lambda: None) -> dict:
    """Clear all local tokens and report the observed remote revocation result."""
    guard()
    store = ChatGPTStore(directory)
    with store.writer():
        current = store.read()
        if current is None:
            return {"status": "signed-out", "remote_revocation": "not-needed"}
        guard()
        client = OAuthClient() if oauth is None else oauth
        try:
            client.revoke(current)
        except ContractError:
            revocation = "unconfirmed"
        else:
            revocation = "confirmed"
        store.clear()
    return {"status": "signed-out", "remote_revocation": revocation}
