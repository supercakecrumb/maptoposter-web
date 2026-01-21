"""Poster service for managing poster generation."""

from typing import Dict, Optional
import uuid
from datetime import datetime
from flask import current_app
from app.models import Job, JobStatus, Poster
from app.extensions import db


class PosterService:
    """Service for poster generation operations."""
    
    def create_poster_job(
        self,
        city: str,
        country: str,
        theme: str,
        distance: int,
        latitude: float,
        longitude: float,
        preview_mode: bool = False,
        session_id: Optional[str] = None,
        page_format: str = 'classic',
        orientation: str = 'portrait',
        dpi: int = 300,
        custom_width_inches: Optional[float] = None,
        custom_height_inches: Optional[float] = None
    ) -> Dict:
        """
        Create a new poster generation job.
        
        Args:
            city: City name
            country: Country name
            theme: Theme name
            distance: Map radius in meters
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            preview_mode: Whether to generate preview (lower res)
            session_id: Session identifier for tracking
            page_format: Page format identifier
            orientation: Portrait or landscape
            dpi: DPI resolution
            custom_width_inches: Width for custom format
            custom_height_inches: Height for custom format
            
        Returns:
            Dict with job_id, status, estimated_duration, etc.
        """
        # Create job record
        job = Job(
            id=str(uuid.uuid4()),
            city=city,
            country=country,
            theme=theme,
            distance=distance,
            latitude=latitude,
            longitude=longitude,
            preview_mode=preview_mode,
            session_id=session_id,
            page_format=page_format,
            orientation=orientation,
            dpi=dpi,
            custom_width_inches=custom_width_inches,
            custom_height_inches=custom_height_inches,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Ensure the job is persisted before queuing
        db.session.flush()
        db.session.refresh(job)
        
        current_app.logger.info(f"Created job {job.id} for {city}, {country}")
        
        # Queue Celery task
        try:
            generate_poster_task = current_app.generate_poster_task
            
            # In eager mode (development), run task in background thread
            # to avoid blocking the HTTP response
            if current_app.config.get('CELERY_TASK_ALWAYS_EAGER'):
                import threading
                def run_task():
                    try:
                        # Small delay to ensure HTTP response returns first
                        import time
                        time.sleep(0.1)
                        generate_poster_task.apply_async(
                            args=[job.id],
                            task_id=job.id
                        )
                    except Exception as e:
                        # Catch any exceptions in the background thread
                        current_app.logger.error(f"Exception in background task for job {job.id}: {e}", exc_info=True)
                        # Update job status to FAILED
                        try:
                            job_record = Job.query.get(job.id)
                            if job_record:
                                job_record.status = JobStatus.FAILED
                                job_record.failed_at = datetime.utcnow()
                                job_record.error_type = type(e).__name__
                                job_record.error_message = str(e)
                                import traceback
                                job_record.error_traceback = traceback.format_exc()
                                db.session.commit()
                        except Exception as db_error:
                            current_app.logger.error(f"Failed to update job status: {db_error}")
                
                thread = threading.Thread(target=run_task, daemon=True)
                thread.start()
                current_app.logger.info(f"Started background thread for job {job.id} (eager mode)")
            else:
                # In production, use Celery normally with countdown
                generate_poster_task.apply_async(
                    args=[job.id],
                    task_id=job.id,
                    countdown=1
                )
                current_app.logger.info(f"Queued Celery task for job {job.id}")
        except Exception as e:
            current_app.logger.error(f"Failed to queue Celery task: {e}")
            job.status = JobStatus.FAILED
            job.error_type = 'QueueError'
            job.error_message = f"Failed to queue task: {str(e)}"
            db.session.commit()
            raise
        
        return {
            'job_id': job.id,
            'status': job.status.value,
            'created_at': job.created_at.isoformat() + 'Z',
            'estimated_duration': 15 if preview_mode else 45,
            'status_url': f'/api/v1/jobs/{job.id}'
        }
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get current job status.
        
        Args:
            job_id: Job UUID
            
        Returns:
            Dict with job status details or None if not found
        """
        job = Job.query.get(job_id)
        if not job:
            return None
        
        result = job.to_dict()
        
        # Add result if completed
        if job.status == JobStatus.COMPLETED and job.poster:
            poster = job.poster
            result['result'] = {
                'poster_id': poster.id,
                'download_url': f'/api/v1/posters/{poster.id}/download',
                'thumbnail_url': f'/api/v1/posters/{poster.id}/thumbnail',
                'preview_url': f'/posters/{poster.id}/preview',
                'filename': poster.filename,
                'file_size': poster.file_size,
                'dimensions': {
                    'width': poster.width,
                    'height': poster.height
                }
            }
        
        return result
    
    def create_batch_poster_job(
        self,
        city: str,
        country: str,
        themes: list,
        distance: int,
        latitude: float,
        longitude: float,
        preview_mode: bool = False,
        session_id: Optional[str] = None,
        page_format: str = 'classic',
        orientation: str = 'portrait',
        dpi: int = 300,
        custom_width_inches: Optional[float] = None,
        custom_height_inches: Optional[float] = None
    ) -> Dict:
        """
        Create a batch poster generation job for multiple themes.
        
        Args:
            city: City name
            country: Country name
            themes: List of theme names
            distance: Map radius in meters
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            preview_mode: Whether to generate preview (lower res)
            session_id: Session identifier for tracking
            page_format: Page format identifier
            orientation: Portrait or landscape
            dpi: DPI resolution
            custom_width_inches: Width for custom format
            custom_height_inches: Height for custom format
            
        Returns:
            Dict with batch_id, job_ids, status, themes, etc.
        """
        # Create a batch ID
        batch_id = str(uuid.uuid4())
        job_ids = []
        
        # Create individual job records for each theme
        for theme in themes:
            job = Job(
                id=str(uuid.uuid4()),
                city=city,
                country=country,
                theme=theme,
                distance=distance,
                latitude=latitude,
                longitude=longitude,
                preview_mode=preview_mode,
                session_id=session_id,
                batch_id=batch_id,
                page_format=page_format,
                orientation=orientation,
                dpi=dpi,
                custom_width_inches=custom_width_inches,
                custom_height_inches=custom_height_inches,
                status=JobStatus.PENDING,
                created_at=datetime.utcnow()
            )
            
            db.session.add(job)
            job_ids.append(job.id)
        
        db.session.commit()
        
        # Ensure all jobs are persisted
        db.session.flush()
        
        current_app.logger.info(f"Created batch {batch_id} with {len(job_ids)} jobs for {city}, {country}")
        
        # Queue Celery task for batch generation
        try:
            # Get the batch task from app
            generate_batch_task = current_app.generate_batch_posters_task
            
            # In eager mode (development), run task in background thread
            if current_app.config.get('CELERY_TASK_ALWAYS_EAGER'):
                import threading
                def run_task():
                    try:
                        import time
                        time.sleep(0.1)
                        generate_batch_task.apply_async(
                            args=[batch_id, job_ids],
                            task_id=batch_id
                        )
                    except Exception as e:
                        current_app.logger.error(f"Exception in background batch task: {e}", exc_info=True)
                        # Update all jobs to FAILED
                        try:
                            for job_id in job_ids:
                                job_record = Job.query.get(job_id)
                                if job_record:
                                    job_record.status = JobStatus.FAILED
                                    job_record.failed_at = datetime.utcnow()
                                    job_record.error_type = type(e).__name__
                                    job_record.error_message = str(e)
                            db.session.commit()
                        except Exception as db_error:
                            current_app.logger.error(f"Failed to update batch job statuses: {db_error}")
                
                thread = threading.Thread(target=run_task, daemon=True)
                thread.start()
                current_app.logger.info(f"Started background thread for batch {batch_id} (eager mode)")
            else:
                # In production, use Celery normally with countdown
                generate_batch_task.apply_async(
                    args=[batch_id, job_ids],
                    task_id=batch_id,
                    countdown=1
                )
                current_app.logger.info(f"Queued Celery batch task {batch_id}")
        except Exception as e:
            current_app.logger.error(f"Failed to queue Celery batch task: {e}")
            # Update all jobs to FAILED
            for job_id in job_ids:
                job_record = Job.query.get(job_id)
                if job_record:
                    job_record.status = JobStatus.FAILED
                    job_record.error_type = 'QueueError'
                    job_record.error_message = f"Failed to queue batch task: {str(e)}"
            db.session.commit()
            raise
        
        # Calculate estimated duration (slightly less than sum of individual jobs due to parallel rendering)
        estimated_duration_per_poster = 15 if preview_mode else 45
        estimated_duration = int(estimated_duration_per_poster * 0.7 * len(themes))  # 30% time savings from batch
        
        return {
            'batch_id': batch_id,
            'job_ids': job_ids,
            'status': 'queued',
            'themes': themes,
            'total_themes': len(themes),
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'estimated_duration': estimated_duration,
            'status_urls': [f'/api/v1/jobs/{job_id}' for job_id in job_ids]
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending/running job.
        
        Args:
            job_id: Job UUID
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        job = Job.query.get(job_id)
        if not job:
            return False
        
        if job.status in [JobStatus.PENDING, JobStatus.PROCESSING]:
            # Revoke Celery task
            try:
                celery = current_app.extensions.get('celery')
                if celery:
                    celery.control.revoke(job_id, terminate=True)
                    current_app.logger.info(f"Revoked Celery task for job {job_id}")
            except Exception as e:
                current_app.logger.error(f"Failed to revoke Celery task: {e}")
            
            # Update job status
            job.status = JobStatus.CANCELLED
            job.failed_at = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"Cancelled job {job_id}")
            return True
        
        return False