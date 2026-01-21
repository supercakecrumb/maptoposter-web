"""Flask application entry point."""

import os
from app import create_app
from app.config import config

# Get environment and config class
env = os.environ.get('FLASK_ENV', 'development')
config_class = config.get(env, config['default'])

# Create Flask app with appropriate config
app = create_app(config_class)

if __name__ == '__main__':
    # Get configuration from environment
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print("=" * 60)
    print("City Map Poster Generator - Web Application")
    print("=" * 60)
    print(f"Starting Flask server on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=debug)