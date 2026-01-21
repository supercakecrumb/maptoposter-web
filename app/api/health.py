"""Health check API endpoints."""

from flask import jsonify, current_app
from app.api import api_v1
from app.extensions import db, get_redis_client
from datetime import datetime


@api_v1.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        JSON response with service health status
    """
    services = {}
    overall_status = 'healthy'
    
    # Check database
    try:
        db.session.execute(db.text('SELECT 1'))
        services['database'] = 'healthy'
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {e}")
        services['database'] = 'unhealthy'
        overall_status = 'degraded'
    
    # Check Redis
    try:
        redis_client = get_redis_client(current_app)
        redis_client.ping()
        services['redis'] = 'healthy'
    except Exception as e:
        current_app.logger.error(f"Redis health check failed: {e}")
        services['redis'] = 'unhealthy'
        overall_status = 'degraded'
    
    # Check Celery (basic check)
    try:
        celery = current_app.extensions.get('celery')
        if celery:
            services['celery'] = 'healthy'
        else:
            services['celery'] = 'unknown'
    except Exception as e:
        current_app.logger.error(f"Celery health check failed: {e}")
        services['celery'] = 'unhealthy'
        overall_status = 'degraded'
    
    # Check storage
    import os
    try:
        storage_path = current_app.config['POSTER_STORAGE_PATH']
        if os.path.exists(storage_path) and os.access(storage_path, os.W_OK):
            services['storage'] = 'healthy'
        else:
            services['storage'] = 'unhealthy'
            overall_status = 'degraded'
    except Exception as e:
        current_app.logger.error(f"Storage health check failed: {e}")
        services['storage'] = 'unhealthy'
        overall_status = 'degraded'
    
    status_code = 200 if overall_status == 'healthy' else 503
    
    return jsonify({
        'status': overall_status,
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'services': services
    }), status_code