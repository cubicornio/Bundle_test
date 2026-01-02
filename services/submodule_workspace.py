# services/submodule_workspace.py
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple

SAFE_RE = re.compile(r"^[a-zA-Z0-9_]+$")


@dataclass
class WorkspaceError(Exception):
    message: str
    status_code: int = 400


class SubmoduleWorkspaceService:
    """
    Regla: 1 submódulo por bundle.

    ✅ Auto-repair:
    - Si falta .selected_submodule.json pero existe un workspace válido en modules/<domain>/<subdomain>,
      lo detecta y lo marca como seleccionado automáticamente.
    - Si el usuario intenta crear un workspace y la carpeta ya existe, en vez de 409 lo "adopta"
      (lo marca seleccionado) y devuelve OK. Esto arregla el caso del reloader.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.modules_root = (self.project_root / "modules").resolve()
        self.selected_file = (self.modules_root / ".selected_submodule.json").resolve()
        self.scaffold_script = (self.project_root / "scaffold_submodule.sh").resolve()

    # -----------------------
    # Helpers
    # -----------------------
    def _safe_name(self, x: str, label: str) -> str:
        x = (x or "").strip()
        if not x or not SAFE_RE.match(x):
            raise WorkspaceError(f"{label} inválido. Usa solo [a-zA-Z0-9_]", 400)
        return x

    def _submodule_path(self, module: str, submodule: str) -> Path:
        target = (self.modules_root / module / submodule).resolve()
        if self.modules_root not in target.parents:
            raise WorkspaceError("Ruta inválida.", 400)
        return target

    def _is_valid_workspace_dir(self, p: Path) -> bool:
        # Marca mínima de "workspace creado"
        return (
            p.exists()
            and p.is_dir()
            and (p / "module.manifest.json").exists()
            and (p / "__init__.py").exists()
        )

    def _discover_existing_workspace(self) -> Optional[Dict[str, Any]]:
        """
        Si NO hay selected_file, intenta encontrar 1 workspace válido existente en modules/*/*.
        Si hay varios, elige el más reciente por mtime del manifest y guarda warning.
        """
        if self.selected_file.exists():
            return None

        if not self.modules_root.exists():
            return None

        candidates: List[Tuple[float, str, str, Path]] = []
        for domain_dir in self.modules_root.iterdir():
            if not domain_dir.is_dir():
                continue
            if domain_dir.name.startswith("."):
                continue

            for sub_dir in domain_dir.iterdir():
                if not sub_dir.is_dir():
                    continue
                if self._is_valid_workspace_dir(sub_dir):
                    try:
                        mtime = (sub_dir / "module.manifest.json").stat().st_mtime
                    except Exception:
                        mtime = 0.0
                    candidates.append((mtime, domain_dir.name, sub_dir.name, sub_dir))

        if not candidates:
            return None

        candidates.sort(reverse=True, key=lambda x: x[0])
        mtime, domain, subdomain, target = candidates[0]

        warning = None
        if len(candidates) > 1:
            warning = (
                "Se detectaron múltiples workspaces en modules/. "
                f"Se seleccionó automáticamente el más reciente: {domain}/{subdomain}. "
                "Si no es el correcto, elimina el workspace y vuelve a seleccionar."
            )

        selected = {
            "id": None,
            "group_name": None,
            "domain": domain,
            "subdomain": subdomain,
            "capability_name": None,
            "repo_url": None,
            "repo_main_branch": "main",
            "repo_visibility": "public",
            "bundle_template": None,
            "local_path": f"modules/{domain}/{subdomain}",
            "auto_repaired": True,
        }
        if warning:
            selected["scaffold_warning"] = warning

        self._save_selected(selected)
        return selected

    # -----------------------
    # Selected handling
    # -----------------------
    def get_selected(self) -> Optional[Dict[str, Any]]:
        """
        Devuelve el seleccionado.
        ✅ Auto-repair si falta el JSON pero existe carpeta creada.
        ✅ Si el JSON existe pero la carpeta ya no existe, se limpia.
        """
        try:
            if self.selected_file.exists():
                data = json.loads(self.selected_file.read_text(encoding="utf-8")) or {}
                domain = (data.get("domain") or "").strip()
                subdomain = (data.get("subdomain") or "").strip()
                if domain and subdomain:
                    target = self._submodule_path(domain, subdomain)
                    if self._is_valid_workspace_dir(target):
                        return data
                    # si ya no existe, limpiamos
                    self.clear_selected()
                    return None
                # json corrupto/incompleto
                self.clear_selected()
                return None
        except Exception:
            # si el archivo está corrupto, lo limpiamos
            try:
                self.clear_selected()
            except Exception:
                pass

        # ✅ si no hay selected_file, intentamos descubrir
        try:
            return self._discover_existing_workspace()
        except Exception:
            return None

    def _save_selected(self, data: Dict[str, Any]) -> None:
        self.modules_root.mkdir(parents=True, exist_ok=True)
        self.selected_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear_selected(self) -> None:
        if self.selected_file.exists():
            self.selected_file.unlink(missing_ok=True)

    # -----------------------
    # Actions
    # -----------------------
    def init_submodule(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Regla: 1 submódulo por bundle
        if self.get_selected():
            raise WorkspaceError(
                "Este bundle ya tiene un submódulo seleccionado. Bórralo antes de elegir otro.",
                409,
            )

        module = self._safe_name(payload.get("domain") or "", "MODULE")
        submodule = self._safe_name(payload.get("subdomain") or "", "SUBMODULE")

        repo_url = (payload.get("repo_url") or "").strip()
        branch = (payload.get("repo_main_branch") or "main").strip() or "main"

        # Asegurar modules/
        self.modules_root.mkdir(parents=True, exist_ok=True)

        if not self.scaffold_script.exists():
            raise WorkspaceError("No existe scaffold_submodule.sh en el root del proyecto.", 500)

        target = self._submodule_path(module, submodule)

        # ✅ Caso clave: la carpeta ya existe (reloader reinició antes de guardar selected)
        # En vez de 409, lo adoptamos como seleccionado si parece válido.
        if target.exists():
            if self._is_valid_workspace_dir(target):
                selected = {
                    "id": payload.get("id"),
                    "group_name": payload.get("group_name"),
                    "domain": module,
                    "subdomain": submodule,
                    "capability_name": payload.get("capability_name"),
                    "repo_url": repo_url or None,
                    "repo_main_branch": branch,
                    "repo_visibility": payload.get("repo_visibility") or "public",
                    "bundle_template": payload.get("bundle_template"),
                    "local_path": f"modules/{module}/{submodule}",
                    "scaffold_warning": (
                        "La carpeta del workspace ya existía (probable reinicio del servidor). "
                        "Se marcó como seleccionado automáticamente."
                    ),
                }
                self._save_selected(selected)
                return selected

            # si existe pero está incompleto, limpiamos y volvemos a crear
            shutil.rmtree(target, ignore_errors=True)

        cmd = ["bash", str(self.scaffold_script), module, submodule]
        if repo_url:
            cmd += [repo_url, branch]

        warning_msg: Optional[str] = None

        try:
            subprocess.run(
                cmd,
                cwd=str(self.project_root),
                check=True,
                capture_output=True,
                text=True,
                env={**os.environ},
            )
        except subprocess.CalledProcessError as e:
            # ✅ WORKAROUND: si el bash falló al final pero el workspace está completo, lo aceptamos
            if self._is_valid_workspace_dir(target):
                raw = (e.stderr or e.stdout or "").strip()
                warning_msg = (raw[:400] if raw else "El scaffold terminó con warning, pero el workspace fue creado.")
            else:
                if target.exists():
                    shutil.rmtree(target, ignore_errors=True)
                msg = (e.stderr or e.stdout or "").strip()[:600] or "Error ejecutando scaffold_submodule.sh"
                raise WorkspaceError(msg, 500)

        selected = {
            "id": payload.get("id"),
            "group_name": payload.get("group_name"),
            "domain": module,
            "subdomain": submodule,
            "capability_name": payload.get("capability_name"),
            "repo_url": repo_url or None,
            "repo_main_branch": branch,
            "repo_visibility": payload.get("repo_visibility") or "public",
            "bundle_template": payload.get("bundle_template"),
            "local_path": f"modules/{module}/{submodule}",
        }
        if warning_msg:
            selected["scaffold_warning"] = warning_msg

        self._save_selected(selected)
        return selected

    def delete_selected(self) -> None:
        selected = self.get_selected()
        if not selected:
            raise WorkspaceError("No hay submódulo seleccionado.", 404)

        module = self._safe_name(selected.get("domain") or "", "MODULE")
        submodule = self._safe_name(selected.get("subdomain") or "", "SUBMODULE")

        target = self._submodule_path(module, submodule)
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)

        # borrar carpeta domain si queda vacía
        module_dir = (self.modules_root / module).resolve()
        try:
            if module_dir.exists() and module_dir.is_dir() and not any(module_dir.iterdir()):
                module_dir.rmdir()
        except Exception:
            pass

        self.clear_selected()
