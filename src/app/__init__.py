from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    from .routes import bp as routes_bp, swaggerui_blueprint, SWAGGER_URL

    # Register the routes blueprint
    app.register_blueprint(routes_bp)

    # Register the Swagger UI blueprint
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # Enable CORS for the entire app
    CORS(app)

    return app
