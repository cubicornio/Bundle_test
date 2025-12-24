# routes/oauth_cubicornio.py
from __future__ import annotations

import secrets
from urllib.parse import urlencode

from flask import (
    Blueprint,
    session,
    redirect,
    url_for,
    request,
    current_app,
)

from oauth_client import oauth


cubicornio_auth_bp = Blueprint(
    "cubicornio_auth",
    __name__,
    url_prefix="/auth/cubicornio",
)


def _pop_next_for_state(state: str | None, default_url: str) -> str:
    """
    Recupera la URL 'next' asociada a un state concreto.
    Si no existe o no hay state, devuelve default_url.
    """
    if not state:
        return default_url

    state_map = session.get("cubi_oauth_states")
    if not isinstance(state_map, dict):
        state_map = {}

    next_url = state_map.pop(state, default_url)
    session["cubi_oauth_states"] = state_map
    return next_url


@cubicornio_auth_bp.route("/login")
def login():
    """
    Inicia el flujo OAuth contra Cubicornio.
    Usa un state aleatorio y lo asocia con la URL 'next' para saber
    a dónde regresar cuando el usuario termine la autorización.
    """
    # A dónde volver en el bundle después del login
    next_url = (
        request.args.get("next")
        or request.referrer
        or url_for("main.home")
    )

    # state único por flujo
    state = secrets.token_urlsafe(16)

    state_map = session.get("cubi_oauth_states")
    if not isinstance(state_map, dict):
        state_map = {}

    state_map[state] = next_url
    session["cubi_oauth_states"] = state_map

    redirect_uri = url_for("cubicornio_auth.callback", _external=True)
    # IMPORTANTE: este redirect_uri debe coincidir EXACTAMENTE
    # con el que registres en Cubicornio

    return oauth.cubicornio.authorize_redirect(
        redirect_uri,
        state=state,
    )


@cubicornio_auth_bp.route("/callback")
def callback():
    """
    Callback que recibe `code` (o `error`) desde Cubicornio.

    - Si error → vuelve a 'next' mostrando el error
    - Si ok   → intercambia code -> token, lo guarda en sesión y vuelve a 'next'
    """
    error = request.args.get("error")
    state = request.args.get("state")

    default_next = url_for("main.home")
    next_url = _pop_next_for_state(state, default_next)

    # Si el usuario canceló en la pantalla de consentimiento
    if error:
        qs = urlencode({"oauth_error": error})
        sep = "&" if "?" in next_url else "?"
        return redirect(f"{next_url}{sep}{qs}")

    # Intercambio code -> token (Authlib valida automáticamente el `state` interno)
    try:
        token = oauth.cubicornio.authorize_access_token()
    except Exception as exc:  # noqa: BLE001
        current_app.logger.exception("Error durante el intercambio code -> token")
        qs = urlencode({"oauth_error": "exchange_failed"})
        sep = "&" if "?" in next_url else "?"
        return redirect(f"{next_url}{sep}{qs}")

    # Guardamos token completo en sesión (access_token, refresh_token, etc.)
    session["cubicornio_token"] = token

    return redirect(next_url)


@cubicornio_auth_bp.route("/logout")
def logout():
    """
    Limpia sólo la sesión local del bundle (no cierra sesión global en Cubicornio).
    """
    session.pop("cubicornio_token", None)
    return redirect(url_for("main.home"))
