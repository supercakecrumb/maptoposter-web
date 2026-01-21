"""Geocoding API endpoints."""

from flask import jsonify, request, current_app
from app.api import api_v1
from app.services.geocoding_service import GeocodingService, GeocodingError, RateLimitExceeded


@api_v1.route('/geocode', methods=['GET'])
def geocode_location():
    """
    Geocode a city and country to coordinates.
    
    Query Parameters:
        city: City name (required)
        country: Country name (required)
        
    Returns:
        JSON response with coordinates and location details
    """
    city = request.args.get('city')
    country = request.args.get('country')
    
    # Validate required parameters
    if not city or not country:
        return jsonify({
            'error': 'Missing parameters',
            'message': 'Both city and country are required'
        }), 400
    
    try:
        geocoding_service = GeocodingService()
        result = geocoding_service.geocode(city, country)
        
        if not result:
            return jsonify({
                'error': 'Location not found',
                'message': f"Could not geocode '{city}, {country}'"
            }), 404
        
        return jsonify(result), 200
        
    except RateLimitExceeded as e:
        current_app.logger.warning(f"Rate limit exceeded for geocoding: {e}")
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Please wait 60 seconds before trying again',
            'retry_after': 60
        }), 429
        
    except GeocodingError as e:
        current_app.logger.error(f"Geocoding error: {e}")
        return jsonify({
            'error': 'Geocoding failed',
            'message': str(e)
        }), 500
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in geocoding: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500