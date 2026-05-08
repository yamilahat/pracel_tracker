from datetime import UTC, datetime

from app.api import gmail
from app.main import create_app
from app.services.gmail_oauth import (
    GmailAuthorizationRequest,
    GmailOAuthTokens,
)
from fastapi.testclient import TestClient


def test_start_gmail_oauth_redirects_and_sets_oauth_cookies(monkeypatch) -> None:
    def fake_build_authorization_request(state: str) -> GmailAuthorizationRequest:
        return GmailAuthorizationRequest(
            authorization_url=f"https://accounts.google.com/o/oauth2/auth?state={state}",
            code_verifier="test-code-verifier",
        )

    monkeypatch.setattr(
        gmail,
        "build_gmail_authorization_request",
        fake_build_authorization_request,
    )

    client = TestClient(create_app(), follow_redirects=False)

    response = client.get("/auth/gmail/start")

    assert response.status_code == 307
    assert response.headers["location"].startswith(
        "https://accounts.google.com/o/oauth2/auth?state="
    )
    assert gmail.OAUTH_STATE_COOKIE_NAME in response.cookies
    assert response.cookies[gmail.OAUTH_CODE_VERIFIER_COOKIE_NAME] == (
        "test-code-verifier"
    )


def test_gmail_oauth_callback_rejects_invalid_state() -> None:
    client = TestClient(create_app())

    response = client.get("/auth/gmail/callback?code=test-code&state=bad-state")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Gmail OAuth state."}


def test_gmail_oauth_callback_requires_code_verifier() -> None:
    client = TestClient(create_app())
    client.cookies.set(gmail.OAUTH_STATE_COOKIE_NAME, "good-state")

    response = client.get("/auth/gmail/callback?code=test-code&state=good-state")

    assert response.status_code == 400
    assert response.json() == {"detail": "Missing Gmail OAuth code verifier."}


def test_gmail_oauth_callback_uses_verifier_and_encrypts_tokens(monkeypatch) -> None:
    encrypted_values: list[str] = []

    def fake_exchange_code_for_tokens(
        code: str,
        code_verifier: str,
    ) -> GmailOAuthTokens:
        assert code == "test-code"
        assert code_verifier == "test-code-verifier"
        return GmailOAuthTokens(
            access_token="raw-access-token",
            refresh_token="raw-refresh-token",
            expires_at=datetime(2026, 5, 8, tzinfo=UTC),
            scopes=["https://www.googleapis.com/auth/gmail.metadata"],
        )

    def fake_encrypt_token(raw_token: str) -> str:
        encrypted_values.append(raw_token)
        return f"encrypted-{raw_token}"

    monkeypatch.setattr(
        gmail,
        "exchange_gmail_code_for_tokens",
        fake_exchange_code_for_tokens,
    )
    monkeypatch.setattr(gmail, "encrypt_token", fake_encrypt_token)

    client = TestClient(create_app())
    client.cookies.set(gmail.OAUTH_STATE_COOKIE_NAME, "good-state")
    client.cookies.set(
        gmail.OAUTH_CODE_VERIFIER_COOKIE_NAME,
        "test-code-verifier",
    )

    response = client.get("/auth/gmail/callback?code=test-code&state=good-state")

    assert response.status_code == 200
    assert response.json() == {
        "status": "connected",
        "provider": "gmail",
        "has_refresh_token": True,
        "expires_at": "2026-05-08T00:00:00+00:00",
    }
    assert encrypted_values == ["raw-access-token", "raw-refresh-token"]
    assert "raw-access-token" not in response.text
    assert "raw-refresh-token" not in response.text
