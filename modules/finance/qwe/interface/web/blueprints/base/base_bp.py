from __future__ import annotations
from flask import Blueprint, render_template

base_bp = Blueprint("finance_qwe_base", __name__, url_prefix="/qwe")

@base_bp.get("/")
def index():
    return render_template("qwe/index.html")
