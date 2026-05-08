from dataclasses import dataclass
from datetime import datetime

from google_auth_oauthlib.flow import Flow

from app.core.settings import get_settings


class GmailOAuthConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class GmailOAuthTokens:
    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    scopes: list[str]


@dataclass(frozen=True)
class GmailAuthorizationRequest:
    authorization_url: str
    code_verifier: str


def _build_client_config() -> dict:
    settings = get_settings()

    if not settings.google_client_id:
        raise GmailOAuthConfigError("GOOGLE_CLIENT_ID is not configured.")
    if not settings.google_client_secret:
        raise GmailOAuthConfigError("GOOGLE_CLIENT_SECRET is not configured.")

    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret.get_secret_value(),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }


def _build_flow(code_verifier: str | None = None) -> Flow:
    settings = get_settings()

    return Flow.from_client_config(
        _build_client_config(),
        scopes=settings.gmail_oauth_scopes,
        redirect_uri=settings.google_redirect_uri,
        code_verifier=code_verifier,
    )


def build_gmail_authorization_request(state: str) -> GmailAuthorizationRequest:
    flow = _build_flow()

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )

    if flow.code_verifier is None:
        raise GmailOAuthConfigError("Google OAuth code verifier was not generated.")

    return GmailAuthorizationRequest(
        authorization_url=authorization_url,
        code_verifier=flow.code_verifier,
    )


def exchange_gmail_code_for_tokens(code: str, code_verifier: str) -> GmailOAuthTokens:
    flow = _build_flow(code_verifier=code_verifier)
    flow.fetch_token(code=code)

    credentials = flow.credentials

    if credentials.token is None:
        raise GmailOAuthConfigError("Google did not return an access token.")

    return GmailOAuthTokens(
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        expires_at=credentials.expiry,
        scopes=list(credentials.scopes or []),
    )
