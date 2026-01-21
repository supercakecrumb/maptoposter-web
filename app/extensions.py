"""Flask extensions initialization."""

from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from celery import Celery, Task
import redis


# Initialize extensions
db = SQLAlchemy()
cache = Cache()


def celery_init_app(app):
    """
    Initialize Celery with Flask application context.
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Celery instance
    """
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def get_redis_client(app):
    """
    Get Redis client instance.
    
    Args:
        app: Flask application instance
        
    Returns:
        Redis client
    """
    return redis.from_url(app.config['REDIS_URL'])