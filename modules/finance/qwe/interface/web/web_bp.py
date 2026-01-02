from __future__ import annotations
from flask import Blueprint

from .blueprints.base.base_bp import base_bp
from .blueprints.registry.registry_bp import registry_bp

web_bp = Blueprint("finance_qwe", __name__)
web_bp.register_blueprint(base_bp)
web_bp.register_blueprint(registry_bp)
