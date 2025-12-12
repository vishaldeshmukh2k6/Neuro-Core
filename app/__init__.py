import os
from flask import Flask
from flask_session import Session
from dotenv import load_dotenv
import redis

load_dotenv()

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key_for_testing_12345")
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600
    
    # Redis configuration for Flask-Session
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    try:
        redis_client = redis.from_url(redis_url)
        redis_client.ping()  # Test connection
        app.config['SESSION_TYPE'] = 'redis'
        app.config['SESSION_REDIS'] = redis_client
        app.config['SESSION_PERMANENT'] = False
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_KEY_PREFIX'] = 'neuro_core:'
        print(f"✅ Connected to Redis at {redis_url}")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        # Fallback to filesystem
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), '..', 'instance', 'sessions')
        os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    Session(app)
    app.config['DEBUG'] = True
    
    # Database configuration
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'chats.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize SQLAlchemy
    from .models import db
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
        print(f"✅ Database tables created at {db_path}")



    # Register blueprints
    from .routes import bp
    from .chat_api import chat_api_bp
    from .session_manager import session_bp
    from .training_routes import training_bp
    app.register_blueprint(bp)
    app.register_blueprint(chat_api_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(training_bp)

    return app
