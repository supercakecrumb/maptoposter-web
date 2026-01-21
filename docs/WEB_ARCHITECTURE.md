
# Flask Web UI Architecture

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Backend Design (Flask)](#2-backend-design-flask)
3. [Frontend Design](#3-frontend-design)
4. [Data Management](#4-data-management)
5. [Key Features by Phase](#5-key-features-by-phase)
6. [Project File Structure](#6-project-file-structure)
7. [Performance & Scalability](#7-performance--scalability)
8. [Security Considerations](#8-security-considerations)
9. [Configuration & Environment](#9-configuration--environment)
10. [Integration with Existing Code](#10-integration-with-existing-code)
11. [Deployment Architecture](#11-deployment-architecture)
12. [Implementation Guidelines](#12-implementation-guidelines)

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Browser                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Frontend (HTML/CSS/JS + Alpine.js)           │  │
│  │  • City Search  • Theme Gallery  • Progress Monitor  │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS/REST API
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application Server                  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │  API Routes    │  │ Business Logic │  │   WebSocket  │ │
│  │  /api/v1/*     │  │  (Services)    │  │  (Optional)  │ │
│  └────────────────┘  └────────────────┘  └──────────────┘ │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │  Auth/Session  │  │  File Manager  │  │   CLI Wrapper│ │
│  └────────────────┘  └────────────────┘  └──────────────┘ │
└────────────┬───────────────────┬──────────────────┬─────────┘
             │                   │                  │
             ▼                   ▼                  ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   PostgreSQL     │  │  Redis Cache     │  │  Celery Workers  │
│   Database       │  │  • Geocoding     │  │  • Poster Gen    │
│  • Jobs          │  │  • OSM Data      │  │  • Preview Gen   │
│  • Posters       │  │  • Sessions      │  │  • Batch Jobs    │
│  • Users         │  │  • Job Status    │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
             │                   │                  │
             └───────────────────┴──────────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   File Storage (Local)   │
                    │   • Generated Posters    │
                    │   • Thumbnails/Previews  │
                    │   • Temporary Files      │
                    └──────────────────────────┘
```

### 1.2 Component Overview

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | HTML5, CSS3, Alpine.js, Tailwind CSS | User interface, forms, interactive elements |
| **Backend API** | Flask 3.x, Flask-RESTful | REST API endpoints, request handling |
| **Background Jobs** | Celery 5.x, Redis | Async poster generation, job queue |
| **Database** | PostgreSQL 15+ (SQLite for dev) | Persistent data storage |
| **Cache** | Redis 7.x | Session storage, data caching, job status |
| **Web Server** | Gunicorn + Nginx | Production WSGI server + reverse proxy |
| **Map Generation** | OSMnx, Matplotlib (existing) | Core poster generation logic |

### 1.3 Technology Stack Rationale

**Why Flask?**
- Lightweight and flexible for this medium-complexity application
- Excellent Python ecosystem integration with existing OSMnx/Matplotlib code
- Easy to extend with Flask extensions
- Lower learning curve than Django for this use case

**Why Celery + Redis?**
- Proven solution for background job processing
- Built-in retry mechanisms and error handling
- Redis provides both caching and message broker functionality
- Scalable worker architecture

**Why Alpine.js over React/Vue?**
- Minimal JavaScript footprint (~15KB)
- Progressive enhancement philosophy
- No build step required (simpler deployment)
- Sufficient for the interactive requirements
- Can be upgraded to React later if needed

---

## 2. Backend Design (Flask)

### 2.1 REST API Endpoints

#### **Base URL**: `/api/v1`

#### 2.1.1 Theme Endpoints

##### `GET /api/v1/themes`
**Description**: List all available themes

**Request**: None

**Response** (200 OK):
```json
{
  "themes": [
    {
      "id": "noir",
      "name": "Noir",
      "description": "Pure black background with white/gray roads",
      "preview_url": "/static/theme-previews/noir.png",
      "colors": {
        "bg": "#000000",
        "text": "#FFFFFF"
      }
    }
  ],
  "total": 17
}
```

**Error Response** (500 Internal Server Error):
```json
{
  "error": "Failed to load themes",
  "message": "Theme directory not accessible"
}
```

---

##### `GET /api/v1/themes/{theme_id}`
**Description**: Get detailed theme information

**Parameters**:
- `theme_id` (path): Theme identifier

**Response** (200 OK):
```json
{
  "id": "noir",
  "name": "Noir",
  "description": "Pure black background with white/gray roads",
  "preview_url": "/static/theme-previews/noir.png",
  "colors": {
    "bg": "#000000",
    "text": "#FFFFFF",
    "water": "#0A0A0A",
    "parks": "#111111",
    "road_motorway": "#FFFFFF",
    "road_primary": "#E0E0E0",
    "road_secondary": "#B0B0B0",
    "road_tertiary": "#808080",
    "road_residential": "#505050",
    "road_default": "#808080"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Theme not found",
  "message": "Theme 'invalid' does not exist"
}
```

---

#### 2.1.2 Geocoding Endpoints

##### `GET /api/v1/geocode`
**Description**: Geocode city name to coordinates

**Query Parameters**:
- `city` (required): City name
- `country` (required): Country name

**Response** (200 OK):
```json
{
  "city": "Paris",
  "country": "France",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "display_name": "Paris, Île-de-France, France",
  "cached": true
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Location not found",
  "message": "Could not geocode 'InvalidCity, NoCountry'"
}
```

**Error Response** (429 Too Many Requests):
```json
{
  "error": "Rate limit exceeded",
  "message": "Please wait 60 seconds before trying again",
  "retry_after": 60
}
```

---

##### `POST /api/v1/geocode/batch`
**Description**: Batch geocode multiple cities (for future use)

**Request Body**:
```json
{
  "locations": [
    {"city": "Paris", "country": "France"},
    {"city": "London", "country": "UK"}
  ]
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "city": "Paris",
      "country": "France",
      "latitude": 48.8566,
      "longitude": 2.3522,
      "success": true
    },
    {
      "city": "London",
      "country": "UK",
      "latitude": 51.5074,
      "longitude": -0.1278,
      "success": true
    }
  ],
  "total": 2,
  "successful": 2,
  "failed": 0
}
```

---

#### 2.1.3 Poster Generation Endpoints

##### `POST /api/v1/posters`
**Description**: Create a new poster generation job

**Request Body**:
```json
{
  "city": "New York",
  "country": "USA",
  "theme": "noir",
  "distance": 12000,
  "latitude": 40.7128,
  "longitude": -74.0060,
  "preview_mode": false
}
```

**Validation Rules**:
- `city`: 1-100 characters, required
- `country`: 1-100 characters, required
- `theme`: Must exist in themes directory, required
- `distance`: 1000-50000 meters, default 29000
- `latitude`: -90 to 90, optional (triggers geocoding if missing)
- `longitude`: -180 to 180, optional
- `preview_mode`: boolean, default false

**Response** (202 Accepted):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-01-19T15:30:00Z",
  "estimated_duration": 45,
  "status_url": "/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "Validation error",
  "message": "Invalid distance value",
  "field": "distance",
  "value": 100000
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Theme not found",
  "message": "Theme 'invalid_theme' does not exist",
  "available_themes": ["noir", "sunset", "blueprint"]
}
```

---

##### `POST /api/v1/posters/preview`
**Description**: Create a quick preview (lower resolution)

**Request Body**: Same as `/api/v1/posters` but forces low resolution

**Response** (202 Accepted):
```json
{
  "job_id": "preview-550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "preview_mode": true,
  "created_at": "2026-01-19T15:30:00Z",
  "estimated_duration": 15
}
```

---

#### 2.1.4 Job Status Endpoints

##### `GET /api/v1/jobs/{job_id}`
**Description**: Get job status and result

**Response** (200 OK) - Pending:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0,
  "created_at": "2026-01-19T15:30:00Z",
  "started_at": null,
  "completed_at": null,
  "estimated_completion": "2026-01-19T15:31:00Z"
}
```

**Response** (200 OK) - Processing:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45,
  "current_step": "Downloading water features",
  "created_at": "2026-01-19T15:30:00Z",
  "started_at": "2026-01-19T15:30:05Z",
  "estimated_completion": "2026-01-19T15:31:00Z"
}
```

**Response** (200 OK) - Completed:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "created_at": "2026-01-19T15:30:00Z",
  "started_at": "2026-01-19T15:30:05Z",
  "completed_at": "2026-01-19T15:30:52Z",
  "duration": 47,
  "result": {
    "poster_id": "abc123",
    "download_url": "/api/v1/posters/abc123/download",
    "thumbnail_url": "/api/v1/posters/abc123/thumbnail",
    "preview_url": "/posters/abc123/preview",
    "filename": "new_york_noir_20260119_153052.png",
    "file_size": 15728640,
    "dimensions": {
      "width": 3600,
      "height": 4800
    }
  }
}
```

**Response** (200 OK) - Failed:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "progress": 30,
  "error": "Network timeout",
  "error_message": "Failed to download OSM data for coordinates (40.7128, -74.0060)",
  "created_at": "2026-01-19T15:30:00Z",
  "started_at": "2026-01-19T15:30:05Z",
  "failed_at": "2026-01-19T15:30:35Z",
  "retry_allowed": true
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Job not found",
  "message": "Job '550e8400-e29b-41d4-a716-446655440000' does not exist"
}
```

---

##### `POST /api/v1/jobs/{job_id}/cancel`
**Description**: Cancel a pending or running job

**Response** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

---

##### `POST /api/v1/jobs/{job_id}/retry`
**Description**: Retry a failed job

**Response** (202 Accepted):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440001",
  "original_job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Job requeued for processing"
}
```

---

#### 2.1.5 Poster Management Endpoints

##### `GET /api/v1/posters`
**Description**: List generated posters (session-based or user-based)

**Query Parameters**:
- `page` (optional): Page number, default 1
- `per_page` (optional): Items per page, default 20, max 100
- `sort` (optional): Sort field (created_at, city, theme), default created_at
- `order` (optional): Sort order (asc, desc), default desc

**Response** (200 OK):
```json
{
  "posters": [
    {
      "id": "abc123",
      "city": "New York",
      "country": "USA",
      "theme": "noir",
      "distance": 12000,
      "created_at": "2026-01-19T15:30:52Z",
      "thumbnail_url": "/api/v1/posters/abc123/thumbnail",
      "preview_url": "/posters/abc123/preview",
      "download_url": "/api/v1/posters/abc123/download",
      "file_size": 15728640
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 42,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

##### `GET /api/v1/posters/{poster_id}`
**Description**: Get poster details

**Response** (200 OK):
```json
{
  "id": "abc123",
  "city": "New York",
  "country": "USA",
  "theme": "noir",
  "distance": 12000,
  "latitude": 40.7128,
  "longitude": -74.0060,
  "created_at": "2026-01-19T15:30:52Z",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "new_york_noir_20260119_153052.png",
  "file_size": 15728640,
  "dimensions": {
    "width": 3600,
    "height": 4800,
    "dpi": 300
  },
  "download_url": "/api/v1/posters/abc123/download",
  "thumbnail_url": "/api/v1/posters/abc123/thumbnail",
  "preview_url": "/posters/abc123/preview"
}
```

---

##### `GET /api/v1/posters/{poster_id}/download`
**Description**: Download full-resolution poster

**Response** (200 OK):
- Content-Type: `image/png`
- Content-Disposition: `attachment; filename="new_york_noir_20260119_153052.png"`
- Binary PNG data

**Response Headers**:
- `Content-Length`: File size in bytes
- `ETag`: File hash for caching
- `Cache-Control`: `public, max-age=31536000` (1 year)

---

##### `GET /api/v1/posters/{poster_id}/thumbnail`
**Description**: Get thumbnail (400px width)

**Response** (200 OK):
- Content-Type: `image/jpeg`
- Binary JPEG data

---

##### `DELETE /api/v1/posters/{poster_id}`
**Description**: Delete a poster (admin/owner only)

**Response** (204 No Content)

---

#### 2.1.6 Health & Status Endpoints

##### `GET /api/v1/health`
**Description**: Health check endpoint

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-19T15:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy",
    "storage": "healthy"
  }
}
```

---

##### `GET /api/v1/stats`
**Description**: System statistics

**Response** (200 OK):
```json
{
  "total_posters": 1247,
  "total_jobs": 1893,
  "active_jobs": 12,
  "cache_hit_rate": 0.87,
  "average_generation_time": 42.5,
  "storage_used": 52428800000,
  "themes_count": 17
}
```

---

### 2.2 Module Structure

```
app/
├── __init__.py              # Flask app factory
├── config.py                # Configuration classes
├── extensions.py            # Flask extensions (SQLAlchemy, Redis, etc.)
│
├── api/                     # API Blueprint
│   ├── __init__.py
│   ├── v1/                  # API version 1
│   │   ├── __init__.py
│   │   ├── themes.py        # Theme endpoints
│   │   ├── geocoding.py     # Geocoding endpoints
│   │   ├── posters.py       # Poster generation endpoints
│   │   ├── jobs.py          # Job status endpoints
│   │   └── health.py        # Health check endpoints
│   └── errors.py            # Error handlers
│
├── services/                # Business logic layer
│   ├── __init__.py
│   ├── theme_service.py     # Theme operations
│   ├── geocoding_service.py # Geocoding with caching
│   ├── poster_service.py    # Poster operations
│   ├── job_service.py       # Job management
│   └── cache_service.py     # Cache operations
│
├── tasks/                   # Celery tasks
│   ├── __init__.py
│   ├── poster_tasks.py      # Poster generation tasks
│   └── cleanup_tasks.py     # Cleanup/maintenance tasks
│
├── models/                  # Database models
│   ├── __init__.py
│   ├── job.py               # Job model
│   ├── poster.py            # Poster model
│   └── session.py           # Session model (optional)
│
├── utils/                   # Utility functions
│   ├── __init__.py
│   ├── validators.py        # Input validation
│   ├── file_manager.py      # File operations
│   └── cli_wrapper.py       # Wrapper for existing CLI code
│
├── web/                     # Web interface (optional)
│   ├── __init__.py
│   ├── routes.py            # Web page routes
│   └── templates/           # Jinja2 templates
│       ├── base.html
│       ├── index.html
│       ├── create.html
│       ├── gallery.html
│       └── poster_detail.html
│
└── static/                  # Static files
    ├── css/
    │   └── main.css
    ├── js/
    │   ├── app.js
    │   └── alpine.min.js
    └── theme-previews/
        ├── noir.png
        └── ...
```

---

### 2.3 Core Service Layer

#### 2.3.1 Theme Service

```python
# app/services/theme_service.py

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from app.utils.cache_service import cache

class ThemeService:
    """Service for theme operations"""
    
    def __init__(self, themes_dir: str = "themes"):
        self.themes_dir = Path(themes_dir)
    
    @cache.memoize(timeout=3600)  # Cache for 1 hour
    def get_all_themes(self) -> List[Dict]:
        """Get all available themes with metadata"""
        themes = []
        for theme_file in sorted(self.themes_dir.glob("*.json")):
            theme_data = self._load_theme_file(theme_file)
            if theme_data:
                themes.append({
                    'id': theme_file.stem,
                    'name': theme_data.get('name', theme_file.stem),
                    'description': theme_data.get('description', ''),
                    'preview_url': f'/static/theme-previews/{theme_file.stem}.png',
                    'colors': {
                        'bg': theme_data.get('bg'),
                        'text': theme_data.get('text')
                    }
                })
        return themes
    
    @cache.memoize(timeout=3600)
    def get_theme(self, theme_id: str) -> Optional[Dict]:
        """Get single theme by ID"""
        theme_file = self.themes_dir / f"{theme_id}.json"
        if not theme_file.exists():
            return None
        
        theme_data = self._load_theme_file(theme_file)
        if theme_data:
            return {
                'id': theme_id,
                'name': theme_data.get('name', theme_id),
                'description': theme_data.get('description', ''),
                'preview_url': f'/static/theme-previews/{theme_id}.png',
                'colors': theme_data
            }
        return None
    
    def _load_theme_file(self, file_path: Path) -> Optional[Dict]:
        """Load and parse theme JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # Log error
            return None
    
    def validate_theme_exists(self, theme_id: str) -> bool:
        """Check if theme exists"""
        return (self.themes_dir / f"{theme_id}.json").exists()
```

---

#### 2.3.2 Geocoding Service

```python
# app/services/geocoding_service.py

from typing import Dict, Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from app.extensions import redis_client
import json

class GeocodingService:
    """Service for geocoding with caching and rate limiting"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="city_map_poster_web")
        self.cache_ttl = 86400 * 30  # 30 days
        self.rate_limit_key = "geocoding:rate_limit"
        self.rate_limit_window = 60  # 1 minute
        self.rate_limit_max = 10  # 10 requests per minute
    
    def geocode(self, city: str, country: str) -> Optional[Dict]:
        """
        Geocode city to coordinates with caching
        
        Returns:
            Dict with latitude, longitude, display_name, cached flag
            None if location not found
        """
        # Check cache first
        cache_key = f"geocode:{city.lower()}:{country.lower()}"
        cached = redis_client.get(cache_key)
        
        if cached:
            result = json.loads(cached)
            result['cached'] = True
            return result
        
        # Check rate limit
        if not self._check_rate_limit():
            raise RateLimitExceeded("Geocoding rate limit exceeded")
        
        # Geocode
        try:
            time.sleep(1)  # Respect Nominatim usage policy
            location = self.geolocator.geocode(f"{city}, {country}")
            
            if not location:
                return None
            
            result = {
                'city': city,
                'country': country,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'display_name': location.address,
                'cached': False
            }
            
            # Cache result
            redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(result)
            )
            
            return result
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            # Log error
            raise GeocodingError(f"Geocoding failed: {str(e)}")
    
    def _check_rate_limit(self) -> bool:
        """Check if rate limit allows request"""
        current = redis_client.incr(self.rate_limit_key)
        if current == 1:
            redis_client.expire(self.rate_limit_key, self.rate_limit_window)
        return current <= self.rate_limit_max

class GeocodingError(Exception):
    pass

class RateLimitExceeded(Exception):
    pass
```

---

#### 2.3.3 Poster Service

```python
# app/services/poster_service.py

from typing import Dict, Optional
import uuid
from datetime import datetime
from app.models.job import Job, JobStatus
from app.models.poster import Poster
from app.tasks.poster_tasks import generate_poster_task
from app.extensions import db

class PosterService:
    """Service for poster generation operations"""
    
    def create_poster_job(
        self,
        city: str,
        country: str,
        theme: str,
        distance: int,
        latitude: float,
        longitude: float,
        preview_mode: bool = False,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Create a new poster generation job
        
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
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Queue Celery task
        generate_poster_task.apply_async(
            args=[job.id],
            task_id=job.id
        )
        
        return {
            'job_id': job.id,
            'status': job.status.value,
            'created_at': job.created_at.isoformat() + 'Z',
            'estimated_duration': 15 if preview_mode else 45,
            'status_url': f'/api/v1/jobs/{job.id}'
        }
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get current job status"""
        job = Job.query.get(job_id)
        if not job:
            return None
        
        result = {
            'job_id': job.id,
            'status': job.status.value,
            'progress': job.progress or 0,
            'created_at': job.created_at.isoformat() + 'Z'
        }
        
        if job.started_at:
            result['started_at'] = job.started_at.isoformat() + 'Z'
        
        if job.status == JobStatus.PROCESSING:
            result['current_step'] = job.current_step
            if job.estimated_completion:
                result['estimated_completion'] = job.estimated_completion.isoformat() + 'Z'
        
        if job.status == JobStatus.COMPLETED:
            result['completed_at'] = job.completed_at.isoformat() + 'Z'
            result['duration'] = (job.completed_at - job.started_at).seconds
            
            # Get poster details
            poster = Poster.query.filter_by(job_id=job.id).first()
            if poster:
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
        
        if job.status == JobStatus.FAILED:
            result['failed_at'] = job.failed_at.isoformat() + 'Z'
            result['error'] = job.error_type
            result['error_message'] = job.error_message
            result['retry_allowed'] = True
        
        return result
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending/running job"""
        job = Job.query.get(job_id)
        if not job:
            return False
        
        if job.status in [JobStatus.PENDING, JobStatus.PROCESSING]:
            # Revoke Celery task
            from app.extensions import celery
            celery.control.revoke(job_id, terminate=True)
            
            # Update job status
            job.status = JobStatus.CANCELLED
            job.failed_at = datetime.utcnow()
            db.session.commit()
            return True
        
        return False
```

---

### 2.4 Background Job Processing (Celery)

#### 2.4.1 Celery Configuration

```python
# app/tasks/__init__.py

from celery import Celery
from app.config import Config

def make_celery(app):
    """Create Celery instance"""
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=600,  # 10 minutes max
        task_soft_time_limit=540,  # 9 minutes soft limit
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=50
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
```

---

#### 2.4.2 Poster Generation Task

```python
# app/tasks/poster_tasks.py

from celery import current_task
from datetime import datetime
from app.extensions import db, celery
from app.models.job import Job, JobStatus
from app.models.poster import Poster
from app.utils.cli_wrapper import PosterGenerator
import traceback

@celery.task(bind=True, max_retries=3)
def generate_poster_task(self, job_id: str):
    """
    Generate poster in background
    
    This task wraps the existing CLI poster generation logic
    """
    job = Job.query.get(job_id)
    if not job:
        return {'error': 'Job not found'}
    
    try:
        # Update job status
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        db.session.commit()
        
        # Initialize poster generator
        generator = PosterGenerator(
            progress_callback=lambda step, progress: update_progress(job_id, step, progress)
        )
        
        # Generate poster
        result = generator.create_poster(
            city=job.city,
            country=job.country,
            theme=job.theme,
            point=(job.latitude, job.longitude),
            distance=job.distance,
            preview_mode=job.preview_mode
        )
        
        # Create poster record
        poster = Poster(
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
            thumbnail_path=result['thumbnail_path'],
            session_id=job.session_id,
            created_at=datetime.utcnow()
        )
        
        # Update job
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.progress = 100
        
        db.session.add(poster)
        db.session.commit()
        
        return {
            'status': 'completed',
            'poster_id': poster.id,
            'filename': poster.filename
        }
        
    except Exception as e:
        # Update job with error
        job.status = JobStatus.FAILED
        job.failed_at = datetime.utcnow()
        job.error_type = type(e).__name__
        job.error_message = str(e)
        job.error_traceback = traceback.format_exc()
        db.session.commit()
        
        # Log error
        print(f"Error generating poster for job {job_id}: {e}")
        
        # Retry if appropriate
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        return {
            'status': 'failed',
            'error': str(e)
        }

def update_progress(job_id: str, step: str, progress: int):
    """Update job progress"""
    job = Job.query.get(job_id)
    if job:
        job.current_step = step
        job.progress = progress
        db.session.commit()
```

---

## 3. Frontend Design

### 3.1 Technology Choice: Alpine.js + Tailwind CSS

**Rationale:**
- **Alpine.js**: Lightweight reactive framework (~15KB) for interactive components
- **Tailwind CSS**: Utility-first CSS for rapid UI development
- **No build step**: Simpler deployment, faster iteration
- **Progressive enhancement**: Works without JavaScript for basic functionality
- **Upgrade path**: Can migrate to React/Vue later if needed

**Alternative for Phase 2**: Consider React for custom theme creator and advanced features

---

### 3.2 Page Structure

#### 3.2.1 Layout Structure

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}City Map Poster Generator{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/tailwind.min.css">
    <link rel="stylesheet" href="/static/css/main.css">
    <script defer src="/static/js/alpine.min.js"></script>
</head>
<body class="bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex">
                    <a href="/" class="flex items-center">
                        <span class="text-xl font-bold">Map Poster</span>
                    </a>
                    <div class="ml-10 flex space-x-8">
                        <a href="/create" class="nav-link">Create</a>
                        <a href="/themes" class="nav-link">Themes</a>
                        <a href="/gallery" class="nav-link">Gallery</a>
                    </div>
                </div>
            </div>
        </div>
    </nav>
    
    <!-- Main Content -->
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer -->
    <footer class="bg-white mt-12">
        <div class="max-w-7xl mx-auto py-6 px-4 text-center text-gray-500">
            <p>&copy; 2026 City Map Poster Generator</p>
        </div>
    </footer>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

---

#### 3.2.2 Home Page (`/`)

**Purpose**: Landing page with hero section and quick start

**Features**:
- Hero section with sample poster images
- Quick create form (city, country, theme)
- Featured themes gallery
- Example posters carousel

**Layout**:
```
┌─────────────────────────────────────────┐
│           Navigation Bar                 │
├─────────────────────────────────────────┤
│                                          │
│         Hero Section                     │
│   "Create Beautiful Map Posters"        │
│   [Sample Poster Images Carousel]       │
│                                          │
│      ┌──────────────────────┐           │
│      │  Quick Create Form   │           │
│      │  City: [_________]   │           │
│      │  Country: [______]   │           │
│      │  Theme: [Dropdown]   │           │
│      │    [Create Poster]   │           │
│      └──────────────────────┘           │
│                                          │
├─────────────────────────────────────────┤
│       Featured Themes Section            │
│   [Noir] [Blueprint] [Sunset] [...]     │
├─────────────────────────────────────────┤
│       Example Posters Gallery            │
│   [Grid of example posters]              │
└─────────────────────────────────────────┘
```

---

#### 3.2.3 Create Page (`/create`)

**Purpose**: Full poster creation form with all options

**Features**:
- City search with autocomplete
- Interactive map for location selection
- Theme selector with live previews
- Distance/radius slider
- Preview mode toggle
- Real-time form validation

**Alpine.js Component**:
```html
<div x-data="posterCreator()">
    <!-- City Search -->
    <div class="mb-6">
        <label class="block text-sm font-medium mb-2">City</label>
        <input 
            type="text" 
            x-model="form.city"
            @input.debounce="searchCity()"
            class="w-full px-4 py-2 border rounded"
            placeholder="Enter city name..."
        >
        <div x-show="suggestions.length" class="autocomplete">
            <template x-for="suggestion in suggestions">
                <div @click="selectCity(suggestion)">
                    <span x-text="suggestion.name"></span>
                </div>
            </template>
        </div>
    </div>
    
    <!-- Theme Selector -->
    <div class="mb-6">
        <label class="block text-sm font-medium mb-2">Theme</label>
        <div class="grid grid-cols-3 gap-4">
            <template x-for="theme in themes">
                <div 
                    @click="form.theme = theme.id"
                    :class="{'ring-2 ring-blue-500': form.theme === theme.id}"
                    class="cursor-pointer rounded-lg overflow-hidden"
                >
                    <img :src="theme.preview_url" :alt="theme.name">
                    <p class="p-2 text-center" x-text="theme.name"></p>
                </div>
            </template>
        </div>
    </div>
    
    <!-- Distance Slider -->
    <div class="mb-6">
        <label class="block text-sm font-medium mb-2">
            Map Radius: <span x-text="form.distance"></span>m
        </label>
        <input 
            type="range" 
            x-model="form.distance"
            min="1000" 
            max="50000" 
            step="1000"
            class="w-full"
        >
        <div class="flex justify-between text-xs text-gray-500">
            <span>1km (small)</span>
            <span>25km (medium)</span>
            <span>50km (large)</span>
        </div>
    </div>
    
    <!-- Submit Button -->
    <button 
        @click="createPoster()"
        :disabled="!canSubmit"
        class="w-full bg-blue-600 text-white py-3 rounded-lg"
    >
        Create Poster
    </button>
</div>
```

---

#### 3.2.4 Theme Gallery Page (`/themes`)

**Purpose**: Browse and preview all themes

**Features**:
- Grid of theme previews
- Filter/search themes
- Theme details modal
- Sample city for each theme

**Layout**:
```
┌─────────────────────────────────────────┐
│    Theme Gallery (17 themes)             │
│    [Search: ___________] [Filter]       │
├─────────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐          │
│  │ Noir │  │ Blue │  │Sunset│          │
│  │[img] │  │[img] │  │[img] │          │
│  └──────┘  └──────┘  └──────┘          │
│  ┌──────┐  ┌──────┐  ┌──────┐          │
│  │Forest│  │ Ocean│  │Autumn│          │
│  │[img] │  │[img] │  │[img] │          │
│  └──────┘  └──────┘  └──────┘          │
└─────────────────────────────────────────┘
```

---

#### 3.2.5 Progress/Generation Page (`/generate/{job_id}`)

**Purpose**: Show real-time poster generation progress

**Features**:
- Progress bar with percentage
- Current step indicator
- Estimated time remaining
- Auto-refresh via polling or WebSocket
- Cancel button

**Alpine.js Component**:
```html
<div x-data="jobMonitor(jobId)" x-init="startPolling()">
    <div class="max-w-2xl mx-auto mt-8">
        <!-- Progress Header -->
        <div class="text-center mb-8">
            <h2 class="text-2xl font-bold mb-2">Generating Your Poster</h2>
            <p class="text-gray-600" x-text="status.current_step"></p>
        </div>
        
        <!-- Progress Bar -->
        <div class="mb-8">
            <div class="bg-gray-200 rounded-full h-4 overflow-hidden">
                <div 
                    class="bg-blue-600 h-full transition-all duration-500"
                    :style="`width: ${status.progress}%`"
                ></div>
            </div>
            <p class="text-center mt-2">
                <span x-text="status.progress"></span>% complete
            </p>
        </div>
        
        <!-- Status Info -->
        <div class="bg-white rounded-lg shadow p-6 mb-4">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <p class="text-sm text-gray-500">City</p>
                    <p class="font-medium" x-text="poster.city"></p>
                </div>
                <div>
                    <p class="text-sm text-gray-500">Theme</p>
                    <p class="font-medium" x-text="poster.theme"></p>
                </div>
                <div>
                    <p class="text-sm text-gray-500">Status</p>
                    <p class="font-medium" x-text="status.status"></p>
                </div>
                <div>
                    <p class="text-sm text-gray-500">Time Elapsed</p>
                    <p class="font-medium" x-text="elapsedTime"></p>
                </div>
            </div>
        </div>
        
        <!-- Actions -->
        <div class="flex justify-center space-x-4">
            <button 
                @click="cancelJob()"
                x-show="status.status === 'processing'"
                class="px-6 py-2 border rounded-lg"
            >
                Cancel
            </button>
        </div>
        
        <!-- Success Modal -->
        <div x-show="status.status === 'completed'" x-transition>
            <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                <div class="bg-white rounded-lg p-8 max-w-md">
                    <h3 class="text-xl font-bold mb-4">Poster Ready!</h3>
                    <a 
                        :href="status.result.download_url"
                        class="block w-full bg-blue-600 text-white text-center py-3 rounded-lg mb-2"
                    >
                        Download Poster
                    </a>
                    <a 
                        :href="`/posters/${status.result.poster_id}`"
                        class="block w-full border text-center py-3 rounded-lg"
                    >
                        View Details
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

#### 3.2.6 Gallery Page (`/gallery`)

**Purpose**: Browse user's generated posters

**Features**:
- Grid of poster thumbnails
- Filter by theme, city, date
- Sort options
- Pagination
- Delete option (with confirmation)

**Layout**:
```
┌─────────────────────────────────────────┐
│    Your Posters (42 total)              │
│    [Filter] [Sort] [Search]             │
├─────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐            │
│  │ New York │  │  Paris   │            │
│  │   Noir   │  │  Sunset  │            │
│  │ [thumb]  │  │ [thumb]  │            │
│  │ [View]   │  │ [View]   │            │
│  └──────────┘  └──────────┘            │
│  ┌──────────┐  ┌──────────┐            │
│  │  Tokyo   │  │  London  │            │
│  │ Japanese │  │Blueprint │            │
│  │ [thumb]  │  │ [thumb]  │            │
│  │ [View]   │  │ [View]   │            │
│  └──────────┘  └──────────┘            │
│                                          │
│       [← Previous] [1] [2] [3] [Next →]│
└─────────────────────────────────────────┘
```

---

#### 3.2.7 Poster Detail Page (`/posters/{poster_id}`)

**Purpose**: View and download individual poster

**Features**:
- Large preview image
- Poster metadata (city, theme, date, dimensions)
- Download full resolution button
- Share buttons (optional)
- Regenerate with different theme button

---

### 3.3 JavaScript Application Logic

```javascript
// static/js/app.js

// Poster Creator Component
function posterCreator() {
    return {
        form: {
            city: '',
            country: '',
            theme: 'noir',
            distance: 29000,
            latitude: null,
            longitude: null
        },
        themes: [],
        suggestions: [],
        loading: false,
        
        async init() {
            // Load themes
            const response = await fetch('/api/v1/themes');
            const data = await response.json();
            this.themes = data.themes;
        },
        
        async searchCity() {
            if (this.form.city.length < 3) {
                this.suggestions = [];
                return;
            }
            
            // Debounced city search
            const response = await fetch(
                `/api/v1/geocode?city=${this.form.city}&country=${this.form.country}`
            );
            
            if (response.ok) {
                const data = await response.json();
                this.suggestions = [data];
            }
        },
        
        selectCity(suggestion) {
            this.form.city = suggestion.city;
            this.form.country = suggestion.country;
            this.form.latitude = suggestion.latitude;
            this.form.longitude = suggestion.longitude;
            this.suggestions = [];
        },
        
        async createPoster() {
            this.loading = true;
            
            try {
                const response = await fetch('/api/v1/posters', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.form)
                });
                
                if (response.ok) {
                    const data = await response.json();
                    // Redirect to progress page
                    window.location.href = `/generate/${data.job_id}`;
                } else {
                    const error = await response.json();
                    alert(`Error: ${error.message}`);
                }
            } finally {
                this.loading = false;
            }
        },
        
        get canSubmit() {
            return this.form.city && 
                   this.form.country && 
                   this.form.theme && 
                   !this.loading;
        }
    };
}

// Job Monitor Component
function jobMonitor(jobId) {
    return {
        jobId: jobId,
        status: {
            status: 'pending',
            progress: 0,
            current_step: 'Initializing...'
        },
        poster: {},
        intervalId: null,
        startTime: Date.now(),
        
        startPolling() {
            this.fetchStatus();
            this.intervalId = setInterval(() => {
                this.fetchStatus();
            }, 2000); // Poll every 2 seconds
        },
        
        async fetchStatus() {
            try {
                const response = await fetch(`/api/v1/jobs/${this.jobId}`);
                const data = await response.json();
                this.status = data;
                
                // Extract poster info
                this.poster = {
                    city: data.city || '',
                    theme: data.theme || ''
                };
                
                // Stop polling if completed or failed
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(this.intervalId);
                }
            } catch (error) {
                console.error('Failed to fetch status:', error);
            }
        },
        
        async cancelJob() {
            if (confirm('Are you sure you want to cancel this job?')) {
                const response = await fetch(`/api/v1/jobs/${this.jobId}/cancel`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    window.location.href = '/';
                }
            }
        },
        
        get elapsedTime() {
            const seconds = Math.floor((Date.now() - this.startTime) / 1000);
            return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
        }
    };
}
```

---

## 4. Data Management

### 4.1 Database Schema

**Database**: PostgreSQL (production), SQLite (development)

#### 4.1.1 Jobs Table

```sql
CREATE TABLE jobs (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    theme VARCHAR(50) NOT NULL,
    distance INTEGER NOT NULL DEFAULT 29000,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    preview_mode BOOLEAN DEFAULT FALSE,
    
    status VARCHAR(20) NOT NULL,  -- pending, processing, completed, failed, cancelled
    progress INTEGER DEFAULT 0,
    current_step VARCHAR(100),
    
    session_id VARCHAR(100),  -- For anonymous users
    user_id INTEGER,  -- For authenticated users (future)
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    estimated_completion TIMESTAMP,
    
    error_type VARCHAR(100),
    error_message TEXT,
    error_traceback TEXT,
    
    INDEX idx_session_id (session_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

---

#### 4.1.2 Posters Table

```sql
CREATE TABLE posters (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    job_id VARCHAR(36) NOT NULL UNIQUE,
    
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    theme VARCHAR(50) NOT NULL,
    distance INTEGER NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,  -- bytes
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    
    thumbnail_path VARCHAR(500),
    preview_path VARCHAR(500),
    
    session_id VARCHAR(100),
    user_id INTEGER,  -- For authenticated users (future)
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP,  -- Last access time
    download_count INTEGER DEFAULT 0,
    
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_city_theme (city, theme),
    INDEX idx_created_at (created_at)
);
```

---

#### 4.1.3 Cache Entries Table (Optional)

```sql
CREATE TABLE cache_entries (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_expires_at (expires_at)
);
```

---

#### 4.1.4 SQLAlchemy Models

```python
# app/models/job.py

from enum import Enum
from datetime import datetime
from app.extensions import db

class JobStatus(Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.String(36), primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    theme = db.Column(db.String(50), nullable=False)
    distance = db.Column(db.Integer, nullable=False, default=29000)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    preview_mode = db.Column(db.Boolean, default=False)
    
    status = db.Column(db.Enum(JobStatus), nullable=False, default=JobStatus.PENDING)
    progress = db.Column(db.Integer, default=0)
    current_step = db.Column(db.String(100))
    
    session_id = db.Column(db.String(100), index=True)
    user_id = db.Column(db.Integer, index=True)  # Future use
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)
    estimated_completion = db.Column(db.DateTime)
    
    error_type = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    error_traceback = db.Column(db.Text)
    
    # Relationship
    poster = db.relationship('Poster', backref='job', uselist=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'country': self.country,
            'theme': self.theme,
            'distance': self.distance,
            'status': self.status.value,
            'progress': self.progress,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

```python
# app/models/poster.py

from datetime import datetime
from app.extensions import db

class Poster(db.Model):
    __tablename__ = 'posters'
    
    id = db.Column(db.String(36), primary_key=True)
    job_id = db.Column(db.String(36), db.ForeignKey('jobs.id'), nullable=False, unique=True)
    
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    theme = db.Column(db.String(50), nullable=False, index=True)
    distance = db.Column(db.Integer, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    
    thumbnail_path = db.Column(db.String(500))
    preview_path = db.Column(db.String(500))
    
    session_id = db.Column(db.String(100), index=True)
    user_id = db.Column(db.Integer, index=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    accessed_at = db.Column(db.DateTime)
    download_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'country': self.country,
            'theme': self.theme,
            'distance': self.distance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'file_size': self.file_size,
            'dimensions': {
                'width': self.width,
                'height': self.height
            }
        }
```

---

### 4.2 Caching Strategy

#### 4.2.1 Redis Cache Structure

```
Key Pattern                              TTL         Purpose
─────────────────────────────────────────────────────────────────
geocode:{city}:{country}                 30 days     Geocoding results
osm_data:{lat}:{lon}:{distance}          7 days      OSM street network
osm_water:{lat}:{lon}:{distance}         7 days      Water features
osm_parks:{lat}:{lon}:{distance}         7 days      Park features
theme:{theme_id}                         1 hour      Theme data
job_status:{job_
id}                      5 min       Job status (hot cache)
session:{session_id}                     24 hours    Session data
rate_limit:{ip}:{endpoint}               1 min       Rate limiting counters
```

### 4.3 File Storage Organization

```
storage/
├── posters/                    # Full resolution posters
│   ├── 2026/                   # Year-based organization
│   │   ├── 01/                 # Month
│   │   │   ├── abc123.png
│   │   │   └── def456.png
│   │   └── 02/
│   └── ...
│
├── thumbnails/                 # 400px wide thumbnails
│   ├── 2026/
│   │   └── 01/
│   │       ├── abc123.jpg
│   │       └── def456.jpg
│   └── ...
│
├── previews/                   # 800px wide previews
│   ├── abc123.jpg
│   └── def456.jpg
│
├── temp/                       # Temporary files (auto-cleanup)
│   └── {job_id}/
│       └── intermediate_files
│
└── theme-previews/             # Static theme preview images
    ├── noir.png
    ├── sunset.png
    └── ...
```

---

## 5. Key Features by Phase

### 5.1 Phase 1: MVP (Minimum Viable Product)

**Timeline**: 2-3 weeks

**Core Features**:
- ✅ Basic poster generation with city, country, theme, distance
- ✅ Theme selection from 17 built-in themes
- ✅ Background job processing with Celery
- ✅ Job status polling and progress tracking
- ✅ Download generated poster
- ✅ Simple responsive UI with Alpine.js
- ✅ Session-based poster history
- ✅ Geocoding with caching

---

### 5.2 Phase 2: Enhanced Features

**Timeline**: 3-4 weeks after Phase 1

**Additional Features**:
- Preview generation at lower resolution (DPI 150)
- Interactive map for precise location selection (Leaflet.js)
- Theme preview gallery with sample cities
- Enhanced geocoding cache
- OSM data caching to reduce API calls
- WebSocket support for real-time progress

---

### 5.3 Phase 3: Advanced Features

**Timeline**: 4-6 weeks after Phase 2

**Power User Features**:
- Custom theme creator
- Batch generation (multiple themes for one city)
- User accounts and authentication
- Advanced customization options

---

## 6. Project File Structure

See section 2.2 for complete file structure.

---

## 7. Performance & Scalability

### 7.1 Caching Strategies

Multi-layer caching as described in section 4.2.

### 7.2 Rate Limiting

Prevent abuse through IP-based and session-based rate limiting.

### 7.3 Async Processing

Celery workers handle all long-running tasks.

---

## 8. Security Considerations

### 8.1 Input Validation

All user inputs validated using Marshmallow schemas.

### 8.2 API Security

- Session-based authentication
- CSRF protection
- Rate limiting
- Content-Type validation

### 8.3 File Security

- Secure filename generation
- File type validation
- Size limits enforced

---

## 9. Configuration & Environment

Environment variables documented in section 9.1.

Configuration classes support development, production, and testing environments.

---

## 10. Integration with Existing Code

### 10.1 CLI Wrapper Service

The [`app/utils/cli_wrapper.py`](../app/utils/cli_wrapper.py) wraps existing [`create_map_poster.py`](../create_map_poster.py) functions without modification.

### 10.2 Backward Compatibility

CLI continues to work exactly as before. Web application imports and wraps functions.

---

## 11. Deployment Architecture

### 11.1 Development Environment

Local development uses Flask development server, Redis, and Celery worker.

### 11.2 Production Deployment

Docker Compose orchestrates:
- Flask application (Gunicorn)
- Celery workers
- PostgreSQL database
- Redis cache
- Nginx reverse proxy

---

## 12. Implementation Guidelines

### 12.1 Implementation Order (Phase 1)

**Week 1: Backend Foundation**
**Week 2: Core Features**
**Week 3: Frontend**
**Week 4: Testing & Polish**

### 12.2 Testing Strategy

Pytest-based testing with fixtures for app, database, and client.

---

## 13. Summary & Next Steps

### 13.1 Architecture Highlights

✅ **Scalable Design**: Async job processing, multi-layer caching, horizontal scaling
✅ **Performance Optimized**: OSM data caching, geocoding cache, thumbnails
✅ **Maintainable Code**: Service layer, CLI wrapper, clear module structure
✅ **Progressive Enhancement**: Phase 1 (3 weeks) → Phase 2 (4 weeks) → Phase 3 (6 weeks)

### 13.2 Implementation Checklist

**Phase 1 (MVP) - 3 Weeks**
- [ ] Setup project structure
- [ ] Implement database models
- [ ] Create API endpoints
- [ ] Wrap CLI code in service layer
- [ ] Implement Celery tasks
- [ ] Build frontend pages
- [ ] Setup caching
- [ ] Deploy to development

### 13.3 Success Metrics

**Technical**:
- Poster generation: < 60s (95th percentile)
- API response: < 200ms (average)
- Cache hit rate: > 80%
- Uptime: > 99.5%

**User**:
- Job completion rate: > 95%
- Time to first poster: < 3 minutes

---

## 14. Reference Links

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-19  
**Author**: Architect Mode  
**Status**: Complete  

**Related Documents**:
- [Technical Overview](TECHNICAL_OVERVIEW.md) - CLI system architecture
- [API Reference](API_REFERENCE.md) - CLI function documentation  
- [Theme System](THEME_SYSTEM.md) - Theme creation guide
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - CLI deployment
- [Future Agents Guide](FUTURE_AGENTS.md) - AI agent reference