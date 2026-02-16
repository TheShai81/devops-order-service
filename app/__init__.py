from flask import Flask
from flask_cors import CORS
from .routes import order_bp


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(order_bp)
    return app
