from __future__ import annotations
from flask import Blueprint, render_template

registry_bp = Blueprint("finance_qwe_registry", __name__, url_prefix="/qwe/registry")

@registry_bp.get("/")
def list_view():
    return render_template("qwe/registry/list.html")

@registry_bp.get("/new")
def new_view():
    return render_template("qwe/registry/form.html")
