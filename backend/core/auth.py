import logging
from typing import Optional

import jwt
import requests
from fastapi import Depends, HTTPException, Request

from core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_jwks_cache: Optional[dict] = None


def _get_jwks(tenant_id: str) -> dict:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
    url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    resp = requests.get(url, timeout=10)
    _jwks_cache = resp.json()
    return _jwks_cache


def _decode_token(token: str, settings: Settings) -> dict:
    """Decode and validate Azure AD JWT token."""
    jwks = _get_jwks(settings.azure_tenant_id)

    # Get the kid from token header
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    # Find matching key
    rsa_key = None
    for key in jwks.get("keys", []):
        if key["kid"] == kid:
            rsa_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
            break

    if not rsa_key:
        raise HTTPException(status_code=401, detail="トークンの署名キーが見つかりません")

    payload = jwt.decode(
        token,
        rsa_key,
        algorithms=["RS256"],
        audience=settings.azure_client_id,
        issuer=f"https://login.microsoftonline.com/{settings.azure_tenant_id}/v2.0",
    )
    return payload


def require_auth(request: Request, settings: Settings = Depends(get_settings)) -> dict:
    """Validate Bearer token. Returns decoded payload. Skips if Entra ID not configured."""
    if not settings.azure_tenant_id or not settings.azure_client_id:
        # Auth not configured — allow all
        return {"name": "anonymous", "groups": []}

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="認証トークンが必要です")

    token = auth_header[7:]
    try:
        payload = _decode_token(token, settings)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="トークンの有効期限が切れています")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"無効なトークンです: {e}")

    return payload


def require_group_member(request: Request, settings: Settings = Depends(get_settings)) -> dict:
    """Require user to be a member of the allowed group. Skips if not configured."""
    if not settings.azure_allowed_group_id:
        return {"name": "anonymous", "groups": []}

    payload = require_auth(request, settings)
    groups = payload.get("groups", [])

    if settings.azure_allowed_group_id not in groups:
        raise HTTPException(status_code=403, detail="このアプリへのアクセス権がありません")

    return payload


def require_admin(request: Request, settings: Settings = Depends(get_settings)) -> dict:
    """Require user to be a member of the admin group. Skips if not configured."""
    if not settings.azure_admin_group_id:
        return require_group_member(request, settings)

    payload = require_auth(request, settings)
    groups = payload.get("groups", [])

    if settings.azure_admin_group_id not in groups:
        raise HTTPException(status_code=403, detail="管理者権限が必要です")

    return payload
