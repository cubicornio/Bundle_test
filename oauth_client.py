# oauth_client.py
from authlib.integrations.flask_client import OAuth


oauth = OAuth()


def register_cubicornio_oauth(app):
    """
    Registra el cliente OAuth de Cubicornio usando la config del app.
    """
    oauth.init_app(app)

    client_id = app.config.get("CUBICORNIO_CLIENT_ID")
    client_secret = app.config.get("CUBICORNIO_CLIENT_SECRET")

    if not client_id or not client_secret:
        app.logger.warning(
            "⚠️ CUBICORNIO_CLIENT_ID / CUBICORNIO_CLIENT_SECRET no configurados. "
            "Edita tu .env antes de intentar loguearte."
        )

    oauth.register(
        name="cubicornio",
        client_id=client_id,
        client_secret=client_secret,
        access_token_url=app.config["CUBICORNIO_OAUTH_TOKEN_URL"],
        authorize_url=app.config["CUBICORNIO_OAUTH_AUTHORIZE_URL"],
        api_base_url=app.config["CUBICORNIO_API_BASE_URL"],
        client_kwargs={
            # Por ahora tu server sólo permite "bundle:read"
            "scope": "bundle:read",
        },
    )
