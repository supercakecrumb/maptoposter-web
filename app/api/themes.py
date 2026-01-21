"""Theme API endpoints."""

from flask import jsonify, current_app
from app.api import api_v1
from app.services.theme_service import ThemeService


@api_v1.route('/themes', methods=['GET'])
def get_themes():
    """
    Get all available themes.
    
    Returns:
        JSON response with list of themes
    """
    try:
        theme_service = ThemeService()
        themes = theme_service.get_all_themes()
        
        return jsonify({
            'themes': themes,
            'total': len(themes)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching themes: {e}")
        return jsonify({
            'error': 'Failed to load themes',
            'message': str(e)
        }), 500


@api_v1.route('/themes/<theme_id>', methods=['GET'])
def get_theme(theme_id):
    """
    Get detailed information about a specific theme.
    
    Args:
        theme_id: Theme identifier
        
    Returns:
        JSON response with theme details
    """
    try:
        theme_service = ThemeService()
        theme = theme_service.get_theme(theme_id)
        
        if not theme:
            return jsonify({
                'error': 'Theme not found',
                'message': f"Theme '{theme_id}' does not exist"
            }), 404
        
        return jsonify(theme), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching theme {theme_id}: {e}")
        return jsonify({
            'error': 'Failed to load theme',
            'message': str(e)
        }), 500