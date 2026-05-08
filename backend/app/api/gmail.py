import secrets

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from app.core.token_encryption import encrypt_token
from app.services.gmail_oauth import (
    GmailOAuthConfigError,
    build_gmail_authorization_request,
    exchange_gmail_code_for_tokens,
)

router = APIRouter(prefix="/auth/gmail", tags=["gmail-auth"])
OAUTH_STATE_COOKIE_NAME = "gmail_oauth_state"
OAUTH_CODE_VERIFIER_COOKIE_NAME = "gmail_oauth_code_verifier"


@router.get("/start")
async def start_gmail_oauth() -> Response:
    state = secrets.token_urlsafe(32)

    try:
        authorization_request = build_gmail_authorization_request(state=state)
    except GmailOAuthConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    response = RedirectResponse(authorization_request.authorization_url)
    response.set_cookie(
        key=OAUTH_STATE_COOKIE_NAME,
        value=state,
        httponly=True,
        samesite="lax",
        max_age=600,
    )
    response.set_cookie(
        key=OAUTH_CODE_VERIFIER_COOKIE_NAME,
        value=authorization_request.code_verifier,
        httponly=True,
        samesite="lax",
        max_age=600,
    )
    return response


@router.get("/callback")
async def handle_gmail_oauth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> dict[str, str | bool | None]:
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth failed: {error}",
        )

    expected_state = request.cookies.get(OAUTH_STATE_COOKIE_NAME)
    code_verifier = request.cookies.get(OAUTH_CODE_VERIFIER_COOKIE_NAME)

    if not state or not expected_state or state != expected_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Gmail OAuth state.",
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth callback did not include a code.",
        )

    if not code_verifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Gmail OAuth code verifier.",
        )

    try:
        tokens = exchange_gmail_code_for_tokens(
            code=code,
            code_verifier=code_verifier,
        )
    except GmailOAuthConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    encrypt_token(tokens.access_token)

    encrypted_refresh_token = None
    if tokens.refresh_token:
        encrypted_refresh_token = encrypt_token(tokens.refresh_token)

    return {
        "status": "connected",
        "provider": "gmail",
        "has_refresh_token": encrypted_refresh_token is not None,
        "expires_at": tokens.expires_at.isoformat() if tokens.expires_at else None,
    }
