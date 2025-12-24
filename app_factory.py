# app_factory.py
from __future__ import annotations

from flask import Flask

from config import Settings
from oauth_client import register_cubicornio_oauth
from routes.main import main_bp
from routes.oauth_cubicornio import cubicornio_auth_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Settings)

    # Config de cookies de sesión
    app.config["SESSION_COOKIE_SECURE"] = Settings.SESSION_COOKIE_SECURE
    app.config["SESSION_COOKIE_HTTPONLY"] = Settings.SESSION_COOKIE_HTTPONLY
    app.config["SESSION_COOKIE_SAMESITE"] = Settings.SESSION_COOKIE_SAMESITE

    # Registrar cliente OAuth de Cubicornio
    register_cubicornio_oauth(app)

    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(cubicornio_auth_bp)

    return app
