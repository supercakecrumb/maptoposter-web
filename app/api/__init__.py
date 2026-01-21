"""API Blueprint registration."""

from flask import Blueprint


# Create API v1 blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')


def register_blueprints(app):
    """
    Register all API blueprints with the Flask app.
    
    Args:
        app: Flask application instance
    """
    # Import route modules to register them with the blueprint
    from app.api import themes, geocoding, posters, jobs, health
    
    # Register API v1 blueprint
    app.register_blueprint(api_v1)
    
    app.logger.info("API blueprints registered")