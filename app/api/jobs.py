"""Job status API endpoints."""

from flask import jsonify, current_app
from app.api import api_v1
from app.services.poster_service import PosterService


@api_v1.route('/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    Get job status and progress.
    
    Args:
        job_id: Job UUID
        
    Returns:
        JSON response with job status details
    """
    try:
        poster_service = PosterService()
        status = poster_service.get_job_status(job_id)
        
        if not status:
            return jsonify({
                'error': 'Job not found',
                'message': f"Job '{job_id}' does not exist"
            }), 404
        
        return jsonify(status), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching job status {job_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to fetch job status'
        }), 500


@api_v1.route('/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """
    Cancel a pending or running job.
    
    Args:
        job_id: Job UUID
        
    Returns:
        JSON response with cancellation status
    """
    try:
        poster_service = PosterService()
        success = poster_service.cancel_job(job_id)
        
        if not success:
            return jsonify({
                'error': 'Cannot cancel job',
                'message': 'Job not found or cannot be cancelled'
            }), 400
        
        return jsonify({
            'job_id': job_id,
            'status': 'cancelled',
            'message': 'Job cancelled successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error cancelling job {job_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to cancel job'
        }), 500