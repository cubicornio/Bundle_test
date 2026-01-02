# routes/submodule_workspace_api.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from flask import Blueprint, jsonify, request, session, current_app

from services.submodule_workspace import SubmoduleWorkspaceService, WorkspaceError
from services.cubicornio_oauth import get_valid_access_token, refresh_and_retry

workspace_api_bp = Blueprint("workspace_api", __name__, url_prefix="/api")

# SOLO esto en .env
CUBICORNIO_BASE_URL =  "https://cubicornio.com"

#  Convención fija (no env)
CUBI_LIST_PATH = "/api/v1/submodules"
CUBI_INIT_PATH_TPL = "/api/v1/submodules/{id}/init"


def _extract_access_token(token_obj: Any) -> Optional[str]:
    if token_obj is None:
        return None
    access = getattr(token_obj, "access_token", None)
    if access:
        return str(access)
    if isinstance(token_obj, dict):
        access = token_obj.get("access_token")
        if access:
            return str(access)
    return None


def _svc() -> SubmoduleWorkspaceService:
    return SubmoduleWorkspaceService(project_root=Path.cwd())


def _cubi_get(path: str, access: str):
    url = f"{CUBICORNIO_BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {access}", "Accept": "application/json"}
    return requests.get(url, headers=headers, timeout=10)


@workspace_api_bp.get("/workspace/selected")
def workspace_selected():
    return jsonify({"selected": _svc().get_selected()}), 200


@workspace_api_bp.post("/workspace/init")
def workspace_init():
    try:
        payload: Dict[str, Any] = request.get_json(force=True) or {}
        selected = _svc().init_submodule(payload)
        return jsonify({"ok": True, "selected": selected}), 200
    except WorkspaceError as e:
        return jsonify({"ok": False, "error": e.message}), e.status_code
    except Exception:
        current_app.logger.exception("workspace_init failed")
        return jsonify({"ok": False, "error": "Error interno"}), 500


@workspace_api_bp.post("/workspace/delete")
def workspace_delete():
    try:
        _svc().delete_selected()
        return jsonify({"ok": True}), 200
    except WorkspaceError as e:
        return jsonify({"ok": False, "error": e.message}), e.status_code
    except Exception:
        current_app.logger.exception("workspace_delete failed")
        return jsonify({"ok": False, "error": "Error interno"}), 500



@workspace_api_bp.get("/submodules/list")
def list_submodules():
    access, _ = get_valid_access_token()
    if not access:
        return jsonify({"ok": False, "error": "oauth_not_connected", "items": []}), 401

    try:
        resp = _cubi_get(CUBI_LIST_PATH, access)

        # fallback 401 -> refresh -> retry
        if resp.status_code == 401:
            new_access = refresh_and_retry()
            if not new_access:
                return jsonify({"ok": False, "error": "oauth_expired_relogin", "items": []}), 401
            resp = _cubi_get(CUBI_LIST_PATH, new_access)

        if not resp.ok:
            return jsonify({
                "ok": False,
                "error": f"API Cubicornio respondió {resp.status_code}: {resp.text[:200]}",
                "items": []
            }), 502

        data = resp.json() or {}
        items = data.get("submodules") or data.get("items") or []
        return jsonify({"ok": True, "items": items}), 200

    except Exception:
        current_app.logger.exception("list_submodules failed")
        return jsonify({"ok": False, "error": "Error consultando Cubicornio API", "items": []}), 502


@workspace_api_bp.get("/submodules/<int:sid>/init")
def init_submodule_payload(sid: int):
    access, _ = get_valid_access_token()
    if not access:
        return jsonify({"ok": False, "error": "oauth_not_connected"}), 401

    path = CUBI_INIT_PATH_TPL.format(id=sid)

    try:
        resp = _cubi_get(path, access)

        # fallback 401 -> refresh -> retry
        if resp.status_code == 401:
            new_access = refresh_and_retry()
            if not new_access:
                return jsonify({"ok": False, "error": "oauth_expired_relogin"}), 401
            resp = _cubi_get(path, new_access)

        if not resp.ok:
            return jsonify({"ok": False, "error": f"API Cubicornio respondió {resp.status_code}: {resp.text[:200]}"}), 502

        data = resp.json() or {}
        payload = data.get("payload")
        if not payload:
            return jsonify({"ok": False, "error": "Payload inválido desde Cubicornio"}), 502

        return jsonify({"ok": True, "payload": payload}), 200

    except Exception:
        current_app.logger.exception("init_submodule_payload failed")
        return jsonify({"ok": False, "error": "Error consultando Cubicornio API"}), 502
