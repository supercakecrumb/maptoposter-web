"""Celery worker entry point."""

import os
import logging
from logging.handlers import RotatingFileHandler
from app import create_app


class DebugFilter(logging.Filter):
    """Filter to only allow DEBUG level logs."""
    def filter(self, record):
        return record.levelno == logging.DEBUG


class InfoAndAboveFilter(logging.Filter):
    """Filter to exclude DEBUG level logs (INFO and above only)."""
    def filter(self, record):
        return record.levelno >= logging.INFO

# Setup Celery logging with split debug and info logs
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configure log format
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Main log handler (INFO and above) - logs/celery.log
main_handler = RotatingFileHandler(
    os.path.join(log_dir, 'celery.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
main_handler.setLevel(logging.INFO)
main_handler.setFormatter(log_format)
main_handler.addFilter(InfoAndAboveFilter())

# Debug log handler (DEBUG only) - logs/celery_debug.log
debug_handler = RotatingFileHandler(
    os.path.join(log_dir, 'celery_debug.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=3
)
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(log_format)
debug_handler.addFilter(DebugFilter())

# Configure Celery logger
celery_logger = logging.getLogger('celery')
celery_logger.setLevel(logging.DEBUG)

# Clear existing handlers to prevent duplicates
if celery_logger.handlers:
    celery_logger.handlers.clear()

celery_logger.addHandler(main_handler)
celery_logger.addHandler(debug_handler)

# Prevent propagation to avoid duplicate logs
celery_logger.propagate = False

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Clear existing handlers to prevent duplicates
if root_logger.handlers:
    root_logger.handlers.clear()

root_logger.addHandler(main_handler)
root_logger.addHandler(debug_handler)

# Create Flask app
app = create_app()

# Push application context
app.app_context().push()

# Get Celery instance
celery = app.extensions.get('celery')

if __name__ == '__main__':
    print("=" * 60)
    print("City Map Poster Generator - Celery Worker")
    print("=" * 60)
    print("Starting Celery worker...")
    print("Broker:", app.config['CELERY_BROKER_URL'])
    print("Backend:", app.config['CELERY_RESULT_BACKEND'])
    print("=" * 60)
    
    # Start worker
    celery.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--max-tasks-per-child=50'
    ])