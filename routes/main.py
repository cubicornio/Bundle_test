# routes/main.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
from flask import Blueprint, render_template, session, request, current_app

from pathlib import Path
from services.submodule_workspace import SubmoduleWorkspaceService

from services.cubicornio_oauth import get_valid_access_token, refresh_and_retry
from services.submodule_guidelines import get_submodule_guidelines

main_bp = Blueprint("main", __name__)

# Base URL de Cubicornio (prod)
CUBICORNIO_BASE_URL = "https://cubicornio.com"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
workspace = SubmoduleWorkspaceService(PROJECT_ROOT)

def _extract_access_token(token_obj: Any) -> Optional[str]:
    """
    Soporta tanto diccionario como el OAuth2Token de Authlib.
    """
    if token_obj is None:
        return None

    # Authlib OAuth2Token soporta acceso por atributo y por key
    access = getattr(token_obj, "access_token", None)
    if access:
        return str(access)

    if isinstance(token_obj, dict):
        access = token_obj.get("access_token")
        if access:
            return str(access)

    return None


def _parse_scopes_from_token(token_obj: Any) -> List[str]:
    """
    Si el servidor no retornara scopes en /profile,
    podemos intentar leerlos de token["scope"] (string).
    """
    if token_obj is None:
        return []

    scope_str = None
    if isinstance(token_obj, dict):
        scope_str = token_obj.get("scope")
    else:
        scope_str = getattr(token_obj, "scope", None)

    if not scope_str:
        return []

    return [s for s in str(scope_str).split() if s.strip()]



def _fetch_cubicornio_profile(token_obj: Any) -> Optional[Dict[str, Any]]:
    """
    Llama a Cubicornio /dev/oauth/profile
    con refresh automático si expira.
    """
    access_token, _ = get_valid_access_token()
    if not access_token:
        return None

    url = f"{CUBICORNIO_BASE_URL}/dev/oauth/profile"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

    try:
        resp = requests.get(url, headers=headers, timeout=5)
    except Exception:
        current_app.logger.exception("Error llamando a Cubicornio /dev/oauth/profile")
        return None

    # ✅ fallback: si Cubicornio dice invalid_token, intenta refresh y reintenta 1 vez
    if resp.status_code == 401:
        new_access = refresh_and_retry()
        if not new_access:
            return None
        headers["Authorization"] = f"Bearer {new_access}"
        resp = requests.get(url, headers=headers, timeout=5)

    if not resp.ok:
        current_app.logger.warning("Cubicornio /profile responded %s: %s", resp.status_code, resp.text[:200])
        return None

    try:
        return resp.json()
    except Exception:
        return None



def _build_context() -> Dict[str, Any]:
    token = session.get("cubicornio_token")
    oauth_error = request.args.get("oauth_error")

    cubi_user = None
    cubi_business = None
    is_owner = False
    scopes: List[str] = []

    if token:
        profile = _fetch_cubicornio_profile(token)
        if profile:
            cubi_user = profile.get("user")
            cubi_business = profile.get("business")
            is_owner = bool(profile.get("is_owner"))
            scopes = profile.get("scopes") or []

            if isinstance(scopes, str):
                scopes = [s for s in scopes.split() if s.strip()]
            elif not isinstance(scopes, list):
                scopes = []

        if not scopes:
            scopes = _parse_scopes_from_token(token)

    return {
        "token": token,
        "oauth_error": oauth_error,
        "cubi_user": cubi_user,
        "cubi_business": cubi_business,
        "is_owner": is_owner,
        "scopes": scopes,
        "cubicornio_url": CUBICORNIO_BASE_URL,
        "selected": workspace.get_selected(),
        "submodules": [],
    }


@main_bp.route("/")
def home():
    # landing igual, solo con sidebar en el template
    return render_template("home.html", **_build_context())


@main_bp.route("/submodules")
def submodules():
    # nueva pantalla (sidebar -> link)
    return render_template("submodules.html", **_build_context())


@main_bp.route("/guidelines")
def guidelines():
    ctx = _build_context()
    ctx["guidelines"] = get_submodule_guidelines()
    return render_template("submodule_guidelines.html", **ctx)
