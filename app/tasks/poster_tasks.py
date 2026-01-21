"""Celery tasks for poster generation."""

from datetime import datetime
import os
import traceback
import uuid
from flask import current_app
from app.extensions import db
from app.models import Job, JobStatus, Poster
from app.services.map_generator import get_coordinates, load_theme, fetch_map_data, render_poster
from app.utils.batch_poster_generator import create_batch_posters
from app.utils.file_helpers import generate_poster_filename, get_poster_path, generate_thumbnail


def update_progress(job_id: str, step: str, progress: int, add_to_steps: bool = True):
    """
    Update job progress in database with detailed step tracking.
    
    Args:
        job_id: Job UUID
        step: Current step description
        progress: Progress percentage (0-100)
        add_to_steps: If True, add this step to progress_steps array
    """
    try:
        job = Job.query.get(job_id)
        if job:
            job.current_step = step
            job.progress = progress
            
            # Add step to progress_steps array if requested
            if add_to_steps:
                if job.progress_steps is None:
                    job.progress_steps = []
                
                # Determine step status based on content
                if step.endswith('✓') or 'downloaded' in step.lower() or 'completed' in step.lower():
                    status = 'completed'
                elif step.endswith('...') or 'processing' in step.lower() or 'rendering' in step.lower():
                    status = 'in_progress'
                else:
                    status = 'pending'
                
                # Add step with timestamp
                step_entry = {
                    'step': step,
                    'status': status,
                    'progress': progress,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                job.progress_steps.append(step_entry)
            
            db.session.commit()
            current_app.logger.info(f"Job {job_id} progress: {progress}% - {step}")
    except Exception as e:
        current_app.logger.error(f"Failed to update progress for job {job_id}: {e}")


def register_tasks(celery_app):
    """
    Register Celery tasks with the app.
    
    This must be called after celery app is created.
    """
    
    @celery_app.task(bind=True, name='app.tasks.generate_batch_posters')
    def generate_batch_posters(self, batch_id: str, job_ids: list):
        """
        Generate batch of posters with different themes in background.
        
        Args:
            batch_id: Batch UUID for tracking
            job_ids: List of job UUIDs for individual themes
            
        Returns:
            Dict with status and results information
        """
        # Get all jobs with retries
        import time
        max_attempts = 5
        jobs = []
        
        for job_id in job_ids:
            for attempt in range(max_attempts):
                db.session.expire_all()
                job = Job.query.get(job_id)
                if job:
                    jobs.append(job)
                    break
                if attempt < max_attempts - 1:
                    current_app.logger.warning(f"Job {job_id} not found, retrying ({attempt + 1}/{max_attempts})")
                    time.sleep(0.5)
            
            if not job:
                current_app.logger.error(f"Job {job_id} not found after {max_attempts} attempts")
        
        if not jobs:
            current_app.logger.error(f"No jobs found for batch {batch_id}")
            return {'error': 'No jobs found'}
        
        # Get common parameters from first job
        first_job = jobs[0]
        city = first_job.city
        country = first_job.country
        distance = first_job.distance
        latitude = first_job.latitude
        longitude = first_job.longitude
        preview_mode = first_job.preview_mode
        session_id = first_job.session_id
        
        # Get format parameters from first job
        from app.utils.format_helpers import get_format_dimensions
        
        width_inches, height_inches = get_format_dimensions(
            format_id=first_job.page_format,
            orientation=first_job.orientation,
            custom_width=first_job.custom_width_inches,
            custom_height=first_job.custom_height_inches
        )
        
        dpi = first_job.dpi
        
        current_app.logger.info(f"Batch format: {width_inches}\" × {height_inches}\" at {dpi} DPI")
        
        # Extract theme list
        themes = [job.theme for job in jobs]
        
        try:
            # Update all jobs to PROCESSING
            for job in jobs:
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"Starting batch poster generation for batch {batch_id}")
            current_app.logger.info(f"Batch details - City: {city}, Country: {country}, Themes: {themes}, Distance: {distance}m")
            
            # Create job map for quick lookup by theme
            job_map = {job.theme: job for job in jobs}
            posters_created = []
            
            # Define job progress callback to update individual jobs
            def job_progress_callback(theme, step_message, progress_percent):
                """Update progress for a specific job by theme"""
                job = job_map.get(theme)
                if job:
                    try:
                        update_progress(job.id, step_message, progress_percent, add_to_steps=True)
                    except Exception as e:
                        current_app.logger.error(f"Error updating progress for job {job.id}: {e}")
            
            # Define result callback to process each poster as it completes
            def result_callback(result):
                """Process each poster result immediately as it completes"""
                theme = result['theme']
                job = job_map.get(theme)
                
                if not job:
                    current_app.logger.warning(f"No job found for theme {theme}")
                    return
                
                current_app.logger.info(f"Processing result for theme {theme}: {result['status']}")
                
                if result['status'] == 'success':
                    # Generate thumbnail
                    thumbnail_path = None
                    try:
                        thumbnail_path = generate_thumbnail(result['file_path'])
                        current_app.logger.info(f"Generated thumbnail for {theme}: {thumbnail_path}")
                    except Exception as e:
                        current_app.logger.warning(f"Failed to generate thumbnail for {theme}: {e}")
                    
                    # Get image dimensions
                    width = result.get('width', int(width_inches * dpi))
                    height = result.get('height', int(height_inches * dpi))
                    
                    # Create poster record
                    poster = Poster(
                        id=str(uuid.uuid4()),
                        job_id=job.id,
                        city=city,
                        country=country,
                        theme=theme,
                        distance=distance,
                        latitude=latitude,
                        longitude=longitude,
                        filename=result['filename'],
                        file_path=result['file_path'],
                        file_size=result['file_size'],
                        width=width,
                        height=height,
                        width_inches=width_inches,
                        height_inches=height_inches,
                        page_format=job.page_format,
                        orientation=job.orientation,
                        dpi=dpi,
                        custom_width_inches=job.custom_width_inches,
                        custom_height_inches=job.custom_height_inches,
                        thumbnail_path=thumbnail_path,
                        session_id=session_id,
                        created_at=datetime.utcnow()
                    )
                    
                    db.session.add(poster)
                    db.session.flush()  # Get poster.id
                    
                    # Update job status immediately
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.utcnow()
                    job.progress = 100
                    job.current_step = f"Complete! {theme}"
                    job.result = {'poster_id': poster.id}
                    
                    # Commit immediately so the UI can show the completed poster
                    db.session.commit()
                    
                    posters_created.append(poster.id)
                    current_app.logger.info(f"Job {job.id} (theme: {theme}) completed successfully. Poster: {poster.id}")
                    
                else:
                    # Update job with error immediately
                    job.status = JobStatus.FAILED
                    job.failed_at = datetime.utcnow()
                    job.error_type = 'BatchGenerationError'
                    job.error_message = result.get('error', 'Unknown error')
                    job.current_step = f"Failed: {theme}"
                    job.progress = 100
                    
                    # Commit immediately so the UI can show the failure
                    db.session.commit()
                    
                    current_app.logger.error(f"Job {job.id} (theme: {theme}) failed: {job.error_message}")
            
            # Generate batch posters with per-job progress and result callbacks
            current_app.logger.info(f"Calling batch poster generator for {len(themes)} themes")
            results = create_batch_posters(
                city=city,
                country=country,
                themes=themes,
                distance=distance,
                preview_mode=preview_mode,
                width_inches=width_inches,
                height_inches=height_inches,
                dpi=dpi,
                progress_callback=None,  # Don't use batch-wide callback
                job_progress_callback=job_progress_callback,  # Update individual jobs
                result_callback=result_callback  # Process results immediately
            )
            current_app.logger.info(f"Batch generation completed for {batch_id}")
            current_app.logger.info(f"Results received for {len(results)} themes")
            
            # All results have been processed incrementally via result_callback
            # Just log the final summary
            current_app.logger.info(f"All jobs processed")
            
            success_count = len(posters_created)
            current_app.logger.info(f"Batch {batch_id} completed: {success_count}/{len(jobs)} posters created")
            
            return {
                'status': 'completed',
                'batch_id': batch_id,
                'total': len(jobs),
                'successful': success_count,
                'poster_ids': posters_created
            }
            
        except Exception as e:
            # Log error with full details
            current_app.logger.error(f"Exception in batch poster generation for batch {batch_id}", exc_info=True)
            current_app.logger.error(f"Error type: {type(e).__name__}")
            current_app.logger.error(f"Error message: {str(e)}")
            
            # Update all jobs with error
            for job in jobs:
                if job.status != JobStatus.COMPLETED:
                    job.status = JobStatus.FAILED
                    job.failed_at = datetime.utcnow()
                    job.error_type = type(e).__name__
                    job.error_message = str(e)
                    job.error_traceback = traceback.format_exc()
            
            db.session.commit()
            
            current_app.logger.info(f"Batch {batch_id} marked as FAILED in database")
            
            return {
                'status': 'failed',
                'error': str(e),
                'batch_id': batch_id
            }
    
    @celery_app.task(bind=True, name='app.tasks.generate_poster')
    def generate_poster(self, job_id: str):
        """
        Generate poster in background.
        
        Args:
            job_id: Job UUID
            
        Returns:
            Dict with status and result information
        """
        # Try to find the job with retries (SQLite cross-process issue)
        import time
        max_attempts = 5
        for attempt in range(max_attempts):
            db.session.expire_all()  # Clear session cache
            job = Job.query.get(job_id)
            if job:
                break
            if attempt < max_attempts - 1:
                current_app.logger.warning(f"Job {job_id} not found, retrying ({attempt + 1}/{max_attempts})")
                time.sleep(0.5)  # Wait 500ms before retry
        
        if not job:
            current_app.logger.error(f"Job {job_id} not found after {max_attempts} attempts")
            return {'error': 'Job not found'}
        
        try:
            # Update job status and initialize progress tracking
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            job.progress_steps = []  # Initialize empty steps array
            db.session.commit()
            
            current_app.logger.info(f"Starting poster generation for job {job_id}")
            current_app.logger.info(f"Job details - City: {job.city}, Country: {job.country}, Theme: {job.theme}, Distance: {job.distance}m")
            
            # Add initial step
            update_progress(job_id, f"Location found: {job.city}, {job.country}", 5)
            
            # Define progress callback
            def progress_callback(step, progress):
                update_progress(job_id, step, progress)
            
            # Step 1: Get coordinates (10%)
            progress_callback("Looking up coordinates", 10)
            point = (job.latitude, job.longitude)
            
            # Step 2: Load theme (20%)
            progress_callback("Loading theme configuration", 20)
            theme_obj = load_theme(job.theme)
            
            # Step 3: Generate filename (25%)
            progress_callback("Preparing output file", 25)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = generate_poster_filename(job.city, job.theme, timestamp)
            output_file = get_poster_path(filename, 'posters')
            
            # Step 4: Fetch map data (30-60%) with detailed callbacks
            progress_callback("Downloading map data (streets, water, parks)...", 30)
            
            def fetch_progress_callback(data_type, completed, total):
                """Handle progress from fetch_map_data"""
                if data_type == 'streets':
                    progress_callback("Streets downloaded ✓", 40)
                elif data_type == 'water':
                    progress_callback("Water features downloaded ✓", 50)
                elif data_type == 'parks':
                    progress_callback("Parks downloaded ✓", 60)
            
            map_data = fetch_map_data(point, job.distance, progress_callback=fetch_progress_callback)
            
            # Step 4.5: Get dimensions from job format parameters
            from app.utils.format_helpers import get_format_dimensions, calculate_output_dimensions
            
            width_inches, height_inches = get_format_dimensions(
                format_id=job.page_format,
                orientation=job.orientation,
                custom_width=job.custom_width_inches,
                custom_height=job.custom_height_inches
            )
            
            # Calculate output pixel dimensions
            width_px, height_px = calculate_output_dimensions(
                width_inches, height_inches, job.dpi
            )
            
            current_app.logger.info(f"Poster dimensions: {width_inches}\" × {height_inches}\" at {job.dpi} DPI = {width_px}×{height_px} pixels")
            
            # Step 5: Render poster (60-90%) with detailed callbacks
            def render_progress_callback(stage):
                """Handle progress from render_poster"""
                if stage == 'initializing':
                    progress_callback(f"Rendering poster with {job.theme} theme...", 65)
                elif stage == 'plotting_features':
                    progress_callback("Plotting water and park features...", 70)
                elif stage == 'plotting_roads':
                    progress_callback("Plotting street network...", 75)
                elif stage == 'adding_gradients':
                    progress_callback("Adding gradients...", 80)
                elif stage == 'adding_typography':
                    progress_callback("Adding typography...", 85)
                elif stage == 'saving':
                    progress_callback("Saving poster...", 90)
            
            render_poster(
                map_data=map_data,
                theme=theme_obj,
                city=job.city,
                country=job.country,
                point=point,
                output_file=output_file,
                width_inches=width_inches,
                height_inches=height_inches,
                dpi=job.dpi,
                progress_callback=render_progress_callback
            )
            
            # Step 6: Verify file was created
            if not os.path.exists(output_file):
                raise FileNotFoundError(f"Poster file was not created: {output_file}")
            
            # Convert to absolute path
            absolute_path = os.path.abspath(output_file)
            
            # Get file info
            file_size = os.path.getsize(absolute_path)
            
            # Use calculated dimensions
            width = width_px
            height = height_px
            
            # Step 7: Generate thumbnail (90-95%)
            progress_callback("Generating thumbnail...", 95)
            
            thumbnail_path = None
            try:
                thumbnail_path = generate_thumbnail(absolute_path)
                thumbnail_path = os.path.abspath(thumbnail_path)
            except Exception as e:
                current_app.logger.warning(f"Failed to generate thumbnail: {e}")
            
            progress_callback("Complete!", 100)
            
            result = {
                'filename': os.path.basename(output_file),
                'file_path': absolute_path,
                'file_size': file_size,
                'width': width,
                'height': height,
                'thumbnail_path': thumbnail_path
            }
            current_app.logger.info(f"Poster generation completed for job {job_id}, file: {result.get('filename')}")
            
            # Create poster record
            poster = Poster(
                id=str(uuid.uuid4()),
                job_id=job.id,
                city=job.city,
                country=job.country,
                theme=job.theme,
                distance=job.distance,
                latitude=job.latitude,
                longitude=job.longitude,
                filename=result['filename'],
                file_path=result['file_path'],
                file_size=result['file_size'],
                width=result['width'],
                height=result['height'],
                width_inches=width_inches,
                height_inches=height_inches,
                page_format=job.page_format,
                orientation=job.orientation,
                dpi=job.dpi,
                custom_width_inches=job.custom_width_inches,
                custom_height_inches=job.custom_height_inches,
                thumbnail_path=result.get('thumbnail_path'),
                session_id=job.session_id,
                created_at=datetime.utcnow()
            )
            
            # Update job with final step
            update_progress(job_id, "Complete!", 100)
            
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = {'poster_id': poster.id}  # Add result for template
            
            db.session.add(poster)
            db.session.commit()
            
            current_app.logger.info(f"Job {job_id} completed successfully. Poster: {poster.id}")
            
            return {
                'status': 'completed',
                'poster_id': poster.id,
                'filename': poster.filename
            }
            
        except Exception as e:
            # Log error with full details
            current_app.logger.error(f"Exception in poster generation for job {job_id}", exc_info=True)
            current_app.logger.error(f"Error type: {type(e).__name__}")
            current_app.logger.error(f"Error message: {str(e)}")
            
            # Update job with error
            job.status = JobStatus.FAILED
            job.failed_at = datetime.utcnow()
            job.error_type = type(e).__name__
            job.error_message = str(e)
            job.error_traceback = traceback.format_exc()
            db.session.commit()
            
            current_app.logger.info(f"Job {job_id} marked as FAILED in database")
            
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    return generate_poster, generate_batch_posters


# Export the task functions for registration
__all__ = ['generate_poster_task', 'generate_batch_posters_task']