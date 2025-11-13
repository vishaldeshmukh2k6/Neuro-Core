import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    
    # Ensure session configuration is correct
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key_for_testing_12345")
    
    # Use default session configuration
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    
    # Enable session debugging
    app.config['DEBUG'] = True

    # Initialize database
    from .database import init_database
    with app.app_context():
        init_database()

    # Register blueprints
    from .routes import bp
    app.register_blueprint(bp)

    return app
