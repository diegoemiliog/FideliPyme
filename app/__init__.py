"""
FideliPyme - Paquete principal de la aplicación.
"""
from flask import Flask


def crear_app():
    """Crea y configura la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='fidelipyme-secret-key',
    )

    # Registrar rutas
    from app.routes.webhook import webhook_bp
    app.register_blueprint(webhook_bp)

    from app.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    return app
