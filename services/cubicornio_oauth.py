# services/cubicornio_oauth.py
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional, Tuple

import requests
from flask import session, current_app

CUBICORNIO_BASE_URL = "https://cubicornio.com"


TOKEN_REFRESH_PATH = "/dev/oauth/token"  # ejemplo

def _access(token_obj: Any) -> Optional[str]:
    if not token_obj:
        return None
    if isinstance(token_obj, dict):
        return token_obj.get("access_token")
    return getattr(token_obj, "access_token", None)

def _refresh(token_obj: Any) -> Optional[str]:
    if not token_obj:
        return None
    if isinstance(token_obj, dict):
        return token_obj.get("refresh_token")
    return getattr(token_obj, "refresh_token", None)

def _is_expired(token_obj: Any, skew_seconds: int = 30) -> bool:
    # Authlib suele guardar expires_at (epoch seconds)
    if not token_obj or not isinstance(token_obj, dict):
        return False
    exp = token_obj.get("expires_at")
    if not exp:
        return False
    try:
        return float(exp) <= (time.time() + skew_seconds)
    except Exception:
        return False

def _do_refresh(refresh_token: str) -> Optional[Dict[str, Any]]:
    # si tu OAuth provider requiere client_id/secret en refresh:
    client_id = os.getenv("CUBICORNIO_CLIENT_ID")
    client_secret = os.getenv("CUBICORNIO_CLIENT_SECRET")

    url = f"{CUBICORNIO_BASE_URL}{TOKEN_REFRESH_PATH}"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    # si tu server exige client creds:
    if client_id:
        data["client_id"] = client_id
    if client_secret:
        data["client_secret"] = client_secret

    r = requests.post(url, data=data, timeout=10)
    if not r.ok:
        current_app.logger.warning("refresh failed %s: %s", r.status_code, r.text[:200])
        return None

    tok = r.json() or {}
    if not tok.get("access_token"):
        return None
    return tok

def get_valid_access_token() -> Tuple[Optional[str], bool]:
    """
    Devuelve (access_token, refreshed_bool)
    Si no hay token o refresh falla, limpia session y devuelve (None, False).
    """
    token = session.get("cubicornio_token")
    access = _access(token)
    if not access:
        return None, False

    # 1) refresh proactivo si expira por expires_at
    if _is_expired(token):
        ref = _refresh(token)
        if not ref:
            session.pop("cubicornio_token", None)
            return None, False

        new_tok = _do_refresh(ref)
        if not new_tok:
            session.pop("cubicornio_token", None)
            return None, False

        session["cubicornio_token"] = new_tok
        return new_tok["access_token"], True

    return access, False

def refresh_and_retry() -> Optional[str]:
    """
    Fallback cuando Cubicornio responde 401 invalid_token.
    Intenta refresh aunque expires_at no esté.
    """
    token = session.get("cubicornio_token")
    ref = _refresh(token)
    if not ref:
        session.pop("cubicornio_token", None)
        return None
    new_tok = _do_refresh(ref)
    if not new_tok:
        session.pop("cubicornio_token", None)
        return None
    session["cubicornio_token"] = new_tok
    return new_tok["access_token"]
