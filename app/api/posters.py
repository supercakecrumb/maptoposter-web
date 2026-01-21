"""Poster API endpoints."""

from flask import jsonify, request, current_app, send_file, session
from app.api import api_v1
from app.services.poster_service import PosterService
from app.services.theme_service import ThemeService
from app.services.geocoding_service import GeocodingService
from app.models import Poster
from app.extensions import db
import os


@api_v1.route('/posters', methods=['POST'])
def create_poster():
    """
    Create a new poster generation job.
    
    Request Body:
        city: City name (required)
        country: Country name (required)
        theme: Theme name (required)
        distance: Map radius in meters (optional, default 29000)
        latitude: Latitude (optional, will geocode if missing)
        longitude: Longitude (optional)
        preview_mode: Boolean for preview mode (optional, default False)
        
    Returns:
        JSON response with job information
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must be JSON'
            }), 400
        
        city = data.get('city')
        country = data.get('country')
        theme = data.get('theme')
        
        if not all([city, country, theme]):
            return jsonify({
                'error': 'Validation error',
                'message': 'city, country, and theme are required'
            }), 400
        
        # Validate theme exists
        theme_service = ThemeService()
        if not theme_service.validate_theme_exists(theme):
            available = [t['id'] for t in theme_service.get_all_themes()]
            return jsonify({
                'error': 'Theme not found',
                'message': f"Theme '{theme}' does not exist",
                'available_themes': available
            }), 404
        
        # Get or validate coordinates
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not latitude or not longitude:
            # Need to geocode
            geocoding_service = GeocodingService()
            geo_result = geocoding_service.geocode(city, country)
            if not geo_result:
                return jsonify({
                    'error': 'Location not found',
                    'message': f"Could not geocode '{city}, {country}'"
                }), 404
            latitude = geo_result['latitude']
            longitude = geo_result['longitude']
        
        # Validate distance
        distance = data.get('distance', current_app.config['DEFAULT_DISTANCE'])
        try:
            distance = int(distance)
            if distance < current_app.config['MIN_DISTANCE'] or distance > current_app.config['MAX_DISTANCE']:
                return jsonify({
                    'error': 'Validation error',
                    'message': f"Distance must be between {current_app.config['MIN_DISTANCE']} and {current_app.config['MAX_DISTANCE']} meters",
                    'field': 'distance',
                    'value': distance
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                'error': 'Validation error',
                'message': 'Distance must be a valid integer',
                'field': 'distance'
            }), 400
        
        preview_mode = data.get('preview_mode', False)
        
        # Get or create session ID
        if 'session_id' not in session:
            import uuid
            session['session_id'] = str(uuid.uuid4())
        session_id = session['session_id']
        
        # Create poster generation job
        poster_service = PosterService()
        result = poster_service.create_poster_job(
            city=city,
            country=country,
            theme=theme,
            distance=distance,
            latitude=latitude,
            longitude=longitude,
            preview_mode=preview_mode,
            session_id=session_id
        )
        
        return jsonify(result), 202
        
    except Exception as e:
        current_app.logger.error(f"Error creating poster job: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to create poster generation job'
        }), 500


@api_v1.route('/posters/<poster_id>', methods=['GET'])
def get_poster(poster_id):
    """
    Get poster details.
    
    Args:
        poster_id: Poster UUID
        
    Returns:
        JSON response with poster details
    """
    try:
        poster = Poster.query.get(poster_id)
        
        if not poster:
            return jsonify({
                'error': 'Poster not found',
                'message': f"Poster '{poster_id}' does not exist"
            }), 404
        
        poster.update_access()
        
        return jsonify(poster.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching poster {poster_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to fetch poster'
        }), 500


@api_v1.route('/posters/<poster_id>/image', methods=['GET'])
def get_poster_image(poster_id):
    """
    Get poster image for display (inline, not as attachment).
    
    Args:
        poster_id: Poster UUID
        
    Returns:
        PNG file inline
    """
    try:
        poster = Poster.query.get(poster_id)
        
        if not poster:
            return jsonify({
                'error': 'Poster not found',
                'message': f"Poster '{poster_id}' does not exist"
            }), 404
        
        if not os.path.exists(poster.file_path):
            current_app.logger.error(f"Poster file not found: {poster.file_path}")
            return jsonify({
                'error': 'File not found',
                'message': 'Poster file is missing on server'
            }), 404
        
        return send_file(
            poster.file_path,
            mimetype='image/png'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error serving poster image {poster_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to serve poster image'
        }), 500


@api_v1.route('/posters/<poster_id>/download', methods=['GET'])
def download_poster(poster_id):
    """
    Download full-resolution poster file.
    
    Args:
        poster_id: Poster UUID
        
    Returns:
        PNG file as attachment
    """
    try:
        poster = Poster.query.get(poster_id)
        
        if not poster:
            return jsonify({
                'error': 'Poster not found',
                'message': f"Poster '{poster_id}' does not exist"
            }), 404
        
        if not os.path.exists(poster.file_path):
            current_app.logger.error(f"Poster file not found: {poster.file_path}")
            return jsonify({
                'error': 'File not found',
                'message': 'Poster file is missing on server'
            }), 404
        
        poster.increment_download_count()
        
        return send_file(
            poster.file_path,
            mimetype='image/png',
            as_attachment=True,
            download_name=poster.filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Error downloading poster {poster_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to download poster'
        }), 500


@api_v1.route('/posters', methods=['GET'])
def list_posters():
    """
    List posters for current session.
    
    Query Parameters:
        page: Page number (default 1)
        per_page: Items per page (default 20, max 100)
        sort: Sort field (default created_at)
        order: Sort order (asc/desc, default desc)
        
    Returns:
        JSON response with paginated poster list
    """
    try:
        # Get session ID
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({
                'posters': [],
                'pagination': {
                    'page': 1,
                    'per_page': 20,
                    'total': 0,
                    'pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }), 200
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        sort = request.args.get('sort', 'created_at')
        order = request.args.get('order', 'desc')
        
        # Build query
        query = Poster.query.filter_by(session_id=session_id)
        
        # Apply sorting
        if sort == 'city':
            sort_column = Poster.city
        elif sort == 'theme':
            sort_column = Poster.theme
        else:
            sort_column = Poster.created_at
        
        if order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        posters = [poster.to_dict() for poster in pagination.items]
        
        return jsonify({
            'posters': posters,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error listing posters: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to list posters'
        }), 500


@api_v1.route('/posters/batch', methods=['POST'])
def create_batch_posters():
    """
    Create multiple posters with different themes for the same location.
    
    Request Body:
        city: City name (required)
        country: Country name (required)
        themes: List of theme names (required, must contain at least one theme)
        distance: Map radius in meters (optional, default 29000)
        latitude: Latitude (optional, will geocode if missing)
        longitude: Longitude (optional)
        preview_mode: Boolean for preview mode (optional, default False)
        
    Returns:
        JSON response with batch job information
        
    Example:
        {
            "city": "Paris",
            "country": "France",
            "themes": ["noir", "midnight_blue", "pastel_dream"],
            "distance": 15000
        }
        
    Response:
        {
            "batch_id": "batch_uuid",
            "job_ids": ["job1_uuid", "job2_uuid", "job3_uuid"],
            "status": "queued",
            "themes": ["noir", "midnight_blue", "pastel_dream"],
            "total_themes": 3,
            "created_at": "2026-01-20T17:00:00Z",
            "estimated_duration": 90
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must be JSON'
            }), 400
        
        city = data.get('city')
        country = data.get('country')
        themes = data.get('themes')
        
        if not all([city, country, themes]):
            return jsonify({
                'error': 'Validation error',
                'message': 'city, country, and themes are required'
            }), 400
        
        # Validate themes is a list with at least one theme
        if not isinstance(themes, list) or len(themes) == 0:
            return jsonify({
                'error': 'Validation error',
                'message': 'themes must be a list with at least one theme'
            }), 400
        
        # Validate that all themes exist
        theme_service = ThemeService()
        available_themes = [t['id'] for t in theme_service.get_all_themes()]
        
        invalid_themes = [t for t in themes if t not in available_themes]
        if invalid_themes:
            return jsonify({
                'error': 'Theme validation error',
                'message': f"Invalid themes: {', '.join(invalid_themes)}",
                'invalid_themes': invalid_themes,
                'available_themes': available_themes
            }), 404
        
        # Get or validate coordinates
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not latitude or not longitude:
            # Need to geocode
            geocoding_service = GeocodingService()
            geo_result = geocoding_service.geocode(city, country)
            if not geo_result:
                return jsonify({
                    'error': 'Location not found',
                    'message': f"Could not geocode '{city}, {country}'"
                }), 404
            latitude = geo_result['latitude']
            longitude = geo_result['longitude']
        
        # Validate distance
        distance = data.get('distance', current_app.config['DEFAULT_DISTANCE'])
        try:
            distance = int(distance)
            if distance < current_app.config['MIN_DISTANCE'] or distance > current_app.config['MAX_DISTANCE']:
                return jsonify({
                    'error': 'Validation error',
                    'message': f"Distance must be between {current_app.config['MIN_DISTANCE']} and {current_app.config['MAX_DISTANCE']} meters",
                    'field': 'distance',
                    'value': distance
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                'error': 'Validation error',
                'message': 'Distance must be a valid integer',
                'field': 'distance'
            }), 400
        
        preview_mode = data.get('preview_mode', False)
        
        # Get or create session ID
        if 'session_id' not in session:
            import uuid
            session['session_id'] = str(uuid.uuid4())
        session_id = session['session_id']
        
        # Create batch poster generation job
        poster_service = PosterService()
        result = poster_service.create_batch_poster_job(
            city=city,
            country=country,
            themes=themes,
            distance=distance,
            latitude=latitude,
            longitude=longitude,
            preview_mode=preview_mode,
            session_id=session_id
        )
        
        return jsonify(result), 202
        
    except Exception as e:
        current_app.logger.error(f"Error creating batch poster job: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to create batch poster generation job'
        }), 500


@api_v1.route('/posters/batch/<batch_id>/status', methods=['GET'])
def get_batch_status(batch_id):
    """
    Get the status of a batch poster generation job.
    
    Args:
        batch_id: Batch UUID
        
    Returns:
        JSON response with batch status and individual job statuses
    """
    try:
        from app.models import Job
        from app.extensions import db
        
        current_app.logger.debug(f"Fetching batch status for batch_id: {batch_id}")
        
        # Get all jobs for this batch
        jobs = Job.query.filter_by(batch_id=batch_id).all()
        
        if not jobs:
            current_app.logger.warning(f"Batch {batch_id} not found")
            return jsonify({
                'error': 'Batch not found',
                'message': f"Batch '{batch_id}' does not exist"
            }), 404
        
        current_app.logger.debug(f"Found {len(jobs)} jobs for batch {batch_id}")
        
        # Get batch metadata from first job
        first_job = jobs[0]
        
        # Build response
        result = {
            'batch_id': batch_id,
            'city': first_job.city,
            'country': first_job.country,
            'themes': [job.theme for job in jobs],
            'total_themes': len(jobs),
            'created_at': first_job.created_at.isoformat() if first_job.created_at else None,
            'jobs': [job.to_dict() for job in jobs]
        }
        
        # Log summary
        statuses = {}
        for job in jobs:
            status = job.status.value if hasattr(job.status, 'value') else str(job.status)
            statuses[status] = statuses.get(status, 0) + 1
        current_app.logger.debug(f"Batch {batch_id} status summary: {statuses}")
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching batch status {batch_id}: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to fetch batch status'
        }), 500


@api_v1.route('/posters/batch/<batch_id>/download', methods=['GET'])
def download_batch_posters(batch_id):
    """
    Download all posters from a batch as a ZIP file.
    
    Args:
        batch_id: Batch UUID
        
    Returns:
        ZIP file containing all completed posters
    """
    try:
        from app.models import Job
        import zipfile
        import io
        from datetime import datetime
        
        # Get all completed jobs for this batch
        jobs = Job.query.filter_by(batch_id=batch_id, status='completed').all()
        
        if not jobs:
            return jsonify({
                'error': 'No completed posters',
                'message': f"Batch '{batch_id}' has no completed posters to download"
            }), 404
        
        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for job in jobs:
                if job.result and 'poster_id' in job.result:
                    poster = Poster.query.get(job.result['poster_id'])
                    if poster and os.path.exists(poster.file_path):
                        # Add poster to ZIP with descriptive filename
                        arcname = f"{poster.city}_{poster.theme}_{poster.created_at.strftime('%Y%m%d_%H%M%S')}.png"
                        zip_file.write(poster.file_path, arcname=arcname)
        
        zip_buffer.seek(0)
        
        # Generate filename
        first_job = jobs[0]
        zip_filename = f"{first_job.city}_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Error downloading batch {batch_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to download batch posters'
        }), 500