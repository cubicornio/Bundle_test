# routes/main.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
from flask import Blueprint, render_template, session, request, current_app


main_bp = Blueprint("main", __name__)

# Base URL de Cubicornio (prod)
CUBICORNIO_BASE_URL = os.getenv("CUBICORNIO_BASE_URL", "https://cubicornio.com").rstrip("/")


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
    Llama a https://cubicornio.com/dev/oauth/profile con el access_token.
    Devuelve dict con {user, business, is_owner, scopes} o None en error.
    """
    access_token = _extract_access_token(token_obj)
    if not access_token:
        return None

    url = f"{CUBICORNIO_BASE_URL}/dev/oauth/profile"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=5)
    except Exception as exc:  # noqa: BLE001
        current_app.logger.exception("Error llamando a Cubicornio /dev/oauth/profile")
        return None

    if not resp.ok:
        current_app.logger.warning(
            "Cubicornio /profile responded with %s: %s",
            resp.status_code,
            resp.text[:300],
        )
        return None

    try:
        data = resp.json()
    except Exception:
        return None

    # Esperamos campos: user, business, is_owner, scopes
    return data


@main_bp.route("/")
def home():
    """
    Landing del bundle:
    - Si no hay token → mostrar botón 'Conectar con Cubicornio'
    - Si hay token → mostrar estado conectado + info básica de usuario/empresa.
    """
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

            # Normalizar scopes a lista de strings
            if isinstance(scopes, str):
                scopes = [s for s in scopes.split() if s.strip()]
            elif not isinstance(scopes, list):
                scopes = []

        # Si por alguna razón /profile no devolvió scopes,
        # los intentamos leer del token OAuth.
        if not scopes:
            scopes = _parse_scopes_from_token(token)

    return render_template(
        "home.html",
        token=token,
        oauth_error=oauth_error,
        cubi_user=cubi_user,
        cubi_business=cubi_business,
        is_owner=is_owner,
        scopes=scopes,
        cubicornio_url=CUBICORNIO_BASE_URL,
    )
