# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Clave de sesión de Flask (NO subir la real a GitHub)
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    # Credenciales de tu OAuth App en Cubicornio
    CUBICORNIO_CLIENT_ID = os.getenv("CUBICORNIO_CLIENT_ID")
    CUBICORNIO_CLIENT_SECRET = os.getenv("CUBICORNIO_CLIENT_SECRET")

    # Endpoints fijos del Authorization Server de Cubicornio
    CUBICORNIO_OAUTH_AUTHORIZE_URL = os.getenv(
        "CUBICORNIO_OAUTH_AUTHORIZE_URL",
        "https://cubicornio.com/dev/oauth/authorize",
    )
    CUBICORNIO_OAUTH_TOKEN_URL = os.getenv(
        "CUBICORNIO_OAUTH_TOKEN_URL",
        "https://cubicornio.com/dev/oauth/token",
    )

    # Base de las APIs de Cubicornio (para cuando expongas endpoints a bundles)
    CUBICORNIO_API_BASE_URL = os.getenv(
        "CUBICORNIO_API_BASE_URL",
        "https://cubicornio.com/api/",
    )

    # Opcional: endurecer cookies en producción
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
