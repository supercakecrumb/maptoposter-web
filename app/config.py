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