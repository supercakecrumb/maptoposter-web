"""Configuration management for Flask application."""

import os
from pathlib import Path


class Config:
    """Base configuration class."""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    BASE_DIR = Path(__file__).parent.parent
    DATABASE_URL = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/posters.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/2'
    
    # Cache
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 3600
    
    # File Storage
    POSTER_STORAGE_PATH = os.environ.get('POSTER_STORAGE_PATH') or str(BASE_DIR / 'posters')
    THUMBNAIL_STORAGE_PATH = os.environ.get('THUMBNAIL_STORAGE_PATH') or str(BASE_DIR / 'thumbnails')
    TEMP_STORAGE_PATH = os.environ.get('TEMP_STORAGE_PATH') or str(BASE_DIR / 'temp')
    
    # Poster Generation
    MAX_DISTANCE = 50000  # meters
    MIN_DISTANCE = 1000   # meters
    DEFAULT_DISTANCE = 29000  # meters
    
    # Page Format Configuration
    PAGE_FORMATS = {
        'classic': {
            'name': 'Classic Poster',
            'width_inches': 12,
            'height_inches': 16,
            'aspect_ratio': 0.75,  # 3:4
            'description': 'Original 12×16 inch format',
            'orientable': True
        },
        'a4': {
            'name': 'A4',
            'width_mm': 210,
            'height_mm': 297,
            'width_inches': 8.27,
            'height_inches': 11.69,
            'aspect_ratio': 0.707,  # √2
            'description': 'Standard A4 (210×297mm)',
            'orientable': True
        },
        'a3': {
            'name': 'A3',
            'width_mm': 297,
            'height_mm': 420,
            'width_inches': 11.69,
            'height_inches': 16.54,
            'aspect_ratio': 0.707,  # √2
            'description': 'Standard A3 (297×420mm)',
            'orientable': True
        },
        'a2': {
            'name': 'A2',
            'width_mm': 420,
            'height_mm': 594,
            'width_inches': 16.54,
            'height_inches': 23.39,
            'aspect_ratio': 0.707,  # √2
            'description': 'Standard A2 (420×594mm)',
            'orientable': True
        },
        '30x40': {
            'name': '30×40 cm',
            'width_cm': 30,
            'height_cm': 40,
            'width_inches': 11.81,
            'height_inches': 15.75,
            'aspect_ratio': 0.75,  # 3:4
            'description': 'Popular print size 30×40cm',
            'orientable': True
        },
        '40x50': {
            'name': '40×50 cm',
            'width_cm': 40,
            'height_cm': 50,
            'width_inches': 15.75,
            'height_inches': 19.69,
            'aspect_ratio': 0.8,  # 4:5
            'description': 'Popular print size 40×50cm',
            'orientable': True
        },
        '50x70': {
            'name': '50×70 cm',
            'width_cm': 50,
            'height_cm': 70,
            'width_inches': 19.69,
            'height_inches': 27.56,
            'aspect_ratio': 0.714,  # 5:7
            'description': 'Popular print size 50×70cm',
            'orientable': True
        },
        'custom': {
            'name': 'Custom Size',
            'description': 'User-defined dimensions',
            'orientable': True,
            'requires_dimensions': True
        }
    }
    
    # DPI Configuration
    DPI_OPTIONS = {
        150: {
            'name': 'Screen/Web (150 DPI)',
            'description': 'Fast preview, suitable for screen viewing',
            'use_cases': ['Digital display', 'Quick preview', 'Social media'],
            'recommended_for': 'Preview and web use',
            'file_size': 'Small (~2-5 MB)',
            'quality': 'Basic'
        },
        300: {
            'name': 'Standard Print (300 DPI)',
            'description': 'Standard print quality for most applications',
            'use_cases': ['Home printing', 'Photo prints', 'Standard posters'],
            'recommended_for': 'Most printing needs',
            'file_size': 'Medium (~8-20 MB)',
            'quality': 'High'
        },
        600: {
            'name': 'Professional Print (600 DPI)',
            'description': 'Highest quality for professional printing',
            'use_cases': ['Commercial printing', 'Gallery quality', 'Fine art'],
            'recommended_for': 'Professional print services',
            'file_size': 'Large (~30-80 MB)',
            'quality': 'Maximum'
        }
    }
    
    # Validation Limits
    MIN_PAGE_SIZE_INCHES = 4    # Minimum 4 inches
    MAX_PAGE_SIZE_INCHES = 48   # Maximum 48 inches (4 feet)
    DEFAULT_PAGE_FORMAT = 'classic'
    DEFAULT_DPI = 300
    DEFAULT_ORIENTATION = 'portrait'
    
    # Rate Limiting
    GEOCODING_RATE_LIMIT = 10  # requests per minute
    API_RATE_LIMIT = 100  # requests per minute
    
    # Session
    SESSION_TYPE = 'redis'
    SESSION_REDIS = None  # Will be set in __init__
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    # Run Celery tasks synchronously in development for easier debugging
    # This allows the app to work without a separate Celery worker process
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously in tests


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}