"""Database models for City Map Poster Generator."""

from enum import Enum
from datetime import datetime
import uuid
from app.extensions import db


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class Job(db.Model):
    """Job model for poster generation tasks."""
    
    __tablename__ = 'jobs'
    
    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Request parameters
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    theme = db.Column(db.String(50), nullable=False)
    distance = db.Column(db.Integer, nullable=False, default=29000)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    preview_mode = db.Column(db.Boolean, default=False)
    
    # Page format fields
    page_format = db.Column(db.String(20), nullable=False, default='classic')
    orientation = db.Column(db.String(10), nullable=False, default='portrait')
    dpi = db.Column(db.Integer, nullable=False, default=300)
    custom_width_inches = db.Column(db.Float, nullable=True)
    custom_height_inches = db.Column(db.Float, nullable=True)
    
    # Job status
    status = db.Column(db.Enum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)
    progress = db.Column(db.Integer, default=0)
    current_step = db.Column(db.String(200))
    progress_steps = db.Column(db.JSON, default=list)  # Array of completed steps with status
    
    # User/session tracking
    session_id = db.Column(db.String(100), index=True)
    user_id = db.Column(db.Integer, index=True)  # For future use
    batch_id = db.Column(db.String(36), nullable=True, index=True)  # UUID for batch grouping
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)
    estimated_completion = db.Column(db.DateTime)
    
    # Error tracking
    error_type = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    error_traceback = db.Column(db.Text)
    
    # Result data (stored as JSON)
    result = db.Column(db.JSON)
    
    # Relationship to Poster
    poster = db.relationship('Poster', backref='job', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Job {self.id} - {self.city}, {self.country} - {self.status.value}>'
    
    def to_dict(self):
        """Convert job to dictionary for API responses."""
        result = {
            'job_id': self.id,
            'city': self.city,
            'country': self.country,
            'theme': self.theme,
            'distance': self.distance,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'status': self.status.value,
            'progress': self.progress or 0,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }
        
        if self.current_step:
            result['current_step'] = self.current_step
        
        if self.progress_steps:
            result['progress_steps'] = self.progress_steps
        
        if self.started_at:
            result['started_at'] = self.started_at.isoformat() + 'Z'
        
        if self.completed_at:
            result['completed_at'] = self.completed_at.isoformat() + 'Z'
            if self.started_at:
                duration = (self.completed_at - self.started_at).total_seconds()
                result['duration'] = int(duration)
        
        if self.failed_at:
            result['failed_at'] = self.failed_at.isoformat() + 'Z'
            result['error'] = self.error_type
            result['error_message'] = self.error_message
            result['retry_allowed'] = True
        
        if self.estimated_completion:
            result['estimated_completion'] = self.estimated_completion.isoformat() + 'Z'
        
        # Include result data (e.g., poster_id for completed jobs)
        if self.result:
            result['result'] = self.result
        
        return result


class Poster(db.Model):
    """Poster model for generated poster metadata."""
    
    __tablename__ = 'posters'
    
    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to Job
    job_id = db.Column(db.String(36), db.ForeignKey('jobs.id'), nullable=False, unique=True)
    
    # Location and theme info
    city = db.Column(db.String(100), nullable=False, index=True)
    country = db.Column(db.String(100), nullable=False)
    theme = db.Column(db.String(50), nullable=False, index=True)
    distance = db.Column(db.Integer, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    # File information
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)  # bytes
    width = db.Column(db.Integer, nullable=False)  # Pixel width
    height = db.Column(db.Integer, nullable=False)  # Pixel height
    
    # Page format fields
    page_format = db.Column(db.String(20), nullable=False, default='classic')
    orientation = db.Column(db.String(10), nullable=False, default='portrait')
    dpi = db.Column(db.Integer, nullable=False, default=300)
    width_inches = db.Column(db.Float, nullable=False, default=12.0)
    height_inches = db.Column(db.Float, nullable=False, default=16.0)
    custom_width_inches = db.Column(db.Float, nullable=True)
    custom_height_inches = db.Column(db.Float, nullable=True)
    
    # Additional file paths
    thumbnail_path = db.Column(db.String(500))
    preview_path = db.Column(db.String(500))
    
    # User/session tracking
    session_id = db.Column(db.String(100), index=True)
    user_id = db.Column(db.Integer, index=True)  # For future use
    
    # Timestamps and access tracking
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    accessed_at = db.Column(db.DateTime)
    download_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Poster {self.id} - {self.city}, {self.theme}>'
    
    def to_dict(self, include_urls=True):
        """Convert poster to dictionary for API responses."""
        result = {
            'id': self.id,
            'city': self.city,
            'country': self.country,
            'theme': self.theme,
            'distance': self.distance,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'filename': self.filename,
            'file_size': self.file_size,
            'page_format': self.page_format,
            'orientation': self.orientation,
            'dpi': self.dpi,
            'dimensions': {
                'width_px': self.width,
                'height_px': self.height,
                'width_inches': self.width_inches,
                'height_inches': self.height_inches,
                'dpi': self.dpi
            },
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'download_count': self.download_count
        }
        
        # Add custom dimensions if applicable
        if self.page_format == 'custom' and self.custom_width_inches and self.custom_height_inches:
            result['custom_dimensions'] = {
                'width_inches': self.custom_width_inches,
                'height_inches': self.custom_height_inches
            }
        
        if include_urls:
            result['download_url'] = f'/api/v1/posters/{self.id}/download'
            result['thumbnail_url'] = f'/api/v1/posters/{self.id}/thumbnail'
            result['preview_url'] = f'/posters/{self.id}/preview'
        
        return result
    
    def update_access(self):
        """Update last accessed timestamp."""
        self.accessed_at = datetime.utcnow()
        db.session.commit()
    
    def increment_download_count(self):
        """Increment download counter."""
        self.download_count += 1
        db.session.commit()