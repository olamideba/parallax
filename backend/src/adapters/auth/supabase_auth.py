from __future__ import annotations

from functools import lru_cache
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from src.config import get_settings

_bearer = HTTPBearer()

# Asymmetric algorithms Supabase uses with JWT signing keys.
_ASYMMETRIC_ALGS = ["ES256", "RS256"]


@lru_cache
def _jwk_client(jwks_url: str) -> PyJWKClient:
    # PyJWKClient caches fetched keys internally; lru_cache reuses the client.
    return PyJWKClient(jwks_url)


def verify_supabase_jwt(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> dict:
    settings = get_settings()
    token = credentials.credentials

    try:
        alg = jwt.get_unverified_header(token).get("alg")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    try:
        if alg == "HS256":
            # Legacy shared-secret signing.
            if not settings.SUPABASE_JWT_SECRET:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SUPABASE_JWT_SECRET is not configured",
                )
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        else:
            # Asymmetric signing keys (current Supabase default) — verify via JWKS.
            if not settings.SUPABASE_URL:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SUPABASE_URL is not configured for JWKS verification",
                )
            jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
            signing_key = _jwk_client(jwks_url).get_signing_key_from_jwt(token).key
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=_ASYMMETRIC_ALGS,
                options={"verify_aud": False},
            )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    return payload


def get_professor_id_from_token(
    payload: Annotated[dict, Depends(verify_supabase_jwt)],
) -> UUID:
    return UUID(payload["sub"])
