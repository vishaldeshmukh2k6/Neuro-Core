import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret")

    # Register blueprints
    from .routes import bp
    app.register_blueprint(bp)

    return app
