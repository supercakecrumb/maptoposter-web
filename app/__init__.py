"""Flask app factory for City Map Poster Generator."""

from flask import Flask
from app.config import Config
from app.extensions import db, cache, celery_init_app
import logging
from logging.handlers import RotatingFileHandler
import os


class DebugFilter(logging.Filter):
    """Filter to only allow DEBUG level logs."""
    def filter(self, record):
        return record.levelno == logging.DEBUG


class InfoAndAboveFilter(logging.Filter):
    """Filter to exclude DEBUG level logs (INFO and above only)."""
    def filter(self, record):
        return record.levelno >= logging.INFO


class WerkzeugFilter(logging.Filter):
    """Filter to exclude werkzeug HTTP request logs from main log."""
    def filter(self, record):
        return record.name != 'werkzeug'


def create_app(config_class=Config):
    """
    Flask application factory.
    
    Args:
        config_class: Configuration class to use
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Setup logging with split debug and info logs
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure log format
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Main log handler (INFO and above) - logs/flask.log
    main_handler = RotatingFileHandler(
        os.path.join(log_dir, 'flask.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    main_handler.setLevel(logging.INFO)
    main_handler.setFormatter(log_format)
    main_handler.addFilter(InfoAndAboveFilter())
    main_handler.addFilter(WerkzeugFilter())  # Filter out werkzeug HTTP request logs
    
    # Debug log handler (DEBUG only) - logs/flask_debug.log
    debug_handler = RotatingFileHandler(
        os.path.join(log_dir, 'flask_debug.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(log_format)
    debug_handler.addFilter(DebugFilter())
    
    # Set app logger level to DEBUG to capture all logs
    app.logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers to prevent duplicates
    if app.logger.handlers:
        app.logger.handlers.clear()
    
    app.logger.addHandler(main_handler)
    app.logger.addHandler(debug_handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    app.logger.propagate = False
    
    # Configure root logger for other modules (e.g., batch_poster_generator)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers and add new ones to prevent duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    root_logger.addHandler(main_handler)
    root_logger.addHandler(debug_handler)
    
    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)
    
    # Initialize Celery
    celery_config = {
        'broker_url': app.config['CELERY_BROKER_URL'],
        'result_backend': app.config['CELERY_RESULT_BACKEND'],
        'task_track_started': True,
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'timezone': 'UTC',
        'enable_utc': True,
    }
    
    # Add eager mode settings for development (run tasks synchronously)
    if app.config.get('CELERY_TASK_ALWAYS_EAGER'):
        celery_config['task_always_eager'] = True
        celery_config['task_eager_propagates'] = app.config.get('CELERY_TASK_EAGER_PROPAGATES', True)
        app.logger.info("Celery configured in eager mode (synchronous task execution)")
    
    app.config.from_mapping(CELERY=celery_config)
    celery = celery_init_app(app)
    
    # Register Celery tasks
    from app.tasks.poster_tasks import register_tasks
    generate_poster_task, generate_batch_posters_task = register_tasks(celery)
    
    # Store task references for access by services
    app.generate_poster_task = generate_poster_task
    app.generate_batch_posters_task = generate_batch_posters_task
    
    # Register blueprints
    from app.api import register_blueprints
    register_blueprints(app)
    
    # Register web routes
    from app.web import web_bp
    app.register_blueprint(web_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        app.logger.info("Database tables created")
    
    app.logger.info(f"Flask app created with config: {config_class.__name__}")
    
    return app