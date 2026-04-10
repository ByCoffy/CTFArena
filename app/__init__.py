from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
socketio = SocketIO()

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, async_mode='threading', cors_allowed_origins='*')

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.challenges import bp as challenges_bp
    app.register_blueprint(challenges_bp, url_prefix='/challenges')

    from app.teams import bp as teams_bp
    app.register_blueprint(teams_bp, url_prefix='/teams')

    from app.leaderboard import bp as leaderboard_bp
    app.register_blueprint(leaderboard_bp, url_prefix='/leaderboard')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.docker_challenges import bp as docker_bp
    app.register_blueprint(docker_bp, url_prefix='/docker')

    # Main routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Register WebSocket events
    from app.docker_challenges.events import register_events
    register_events(socketio)

    # Custom Jinja filters
    import json as _json
    app.jinja_env.filters['from_json'] = lambda s: _json.loads(s) if s else {}

    # Context processor for templates
    @app.context_processor
    def inject_ctf_info():
        return {
            'ctf_name': app.config['CTF_NAME'],
            'ctf_description': app.config['CTF_DESCRIPTION']
        }

    # Start cleanup scheduler
    _start_cleanup_scheduler(app)

    return app


def _start_cleanup_scheduler(app):
    """Start a background thread that cleans up expired Docker containers."""
    import threading

    def cleanup_loop():
        import time
        while True:
            time.sleep(60)
            try:
                from app.services.docker_service import DockerService
                cleaned = DockerService.cleanup_expired(app)
                if cleaned > 0:
                    app.logger.info(f"Cleaned up {cleaned} expired Docker instances")
            except Exception as e:
                app.logger.debug(f"Cleanup cycle skipped: {e}")

    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()


from app import models
