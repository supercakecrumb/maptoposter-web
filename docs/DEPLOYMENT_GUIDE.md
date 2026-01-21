# Deployment Guide

Complete installation and deployment instructions for the City Map Poster Generator.

## Table of Contents

- [Deployment Guide](#deployment-guide)
  - [Table of Contents](#table-of-contents)
  - [System Requirements](#system-requirements)
    - [Minimum Requirements](#minimum-requirements)
    - [Python Version Support](#python-version-support)
    - [Platform Support](#platform-support)
  - [Quick Start](#quick-start)
    - [CLI Quick Start](#cli-quick-start)
    - [Web Application Quick Start](#web-application-quick-start)
    - [Docker Quick Start](#docker-quick-start)
  - [Installation Methods](#installation-methods)
    - [Standard Installation](#standard-installation)
      - [Step 1: Verify Python Installation](#step-1-verify-python-installation)
      - [Step 2: Download Project](#step-2-download-project)
      - [Step 3: Install Dependencies](#step-3-install-dependencies)
      - [Step 4: Verify Installation](#step-4-verify-installation)
    - [Virtual Environment Installation](#virtual-environment-installation)
      - [Using venv (Built-in)](#using-venv-built-in)
      - [Using virtualenv](#using-virtualenv)
    - [Conda Installation](#conda-installation)
  - [Web Application Setup](#web-application-setup)
    - [Local Development Setup](#local-development-setup)
      - [Step 1: Install Web Dependencies](#step-1-install-web-dependencies)
    - [Redis Installation](#redis-installation)
    - [PostgreSQL Setup (Optional)](#postgresql-setup-optional)
    - [Running the Web Application](#running-the-web-application)
      - [Terminal 1: Flask Web Server](#terminal-1-flask-web-server)
      - [Terminal 2: Celery Worker](#terminal-2-celery-worker)
      - [Terminal 3: Redis Server (if not running as service)](#terminal-3-redis-server-if-not-running-as-service)
    - [Environment Configuration](#environment-configuration)
    - [Verify Web Application](#verify-web-application)
  - [Docker Deployment](#docker-deployment)
    - [Docker Prerequisites](#docker-prerequisites)
    - [Development Mode](#development-mode)
    - [Production Mode](#production-mode)
    - [Production with Nginx](#production-with-nginx)
    - [Scaling](#scaling)
    - [Docker Management Commands](#docker-management-commands)
    - [Docker Troubleshooting](#docker-troubleshooting)
  - [Dependency Management](#dependency-management)
    - [Core Dependencies](#core-dependencies)
    - [Dependency Tree](#dependency-tree)
    - [Version Pinning Strategy](#version-pinning-strategy)
    - [Updating Dependencies](#updating-dependencies)
  - [Configuration](#configuration)
    - [Directory Structure](#directory-structure)
    - [Configuration Constants](#configuration-constants)
    - [Environment Variables](#environment-variables)
  - [Verification](#verification)
    - [Post-Installation Checks](#post-installation-checks)
      - [1. Check Python Version](#1-check-python-version)
      - [2. Verify Dependencies](#2-verify-dependencies)
      - [3. Check File Structure](#3-check-file-structure)
      - [4. List Available Themes](#4-list-available-themes)
      - [5. Test Run (Quick)](#5-test-run-quick)
    - [Health Check Script](#health-check-script)
      - [Celery Worker Not Starting](#celery-worker-not-starting)
      - [Database Errors](#database-errors)
      - [Import Errors](#import-errors)
      - [Port Already in Use](#port-already-in-use)
      - [Tasks Failing](#tasks-failing)
      - [Performance Issues](#performance-issues)
    - [Docker Troubleshooting](#docker-troubleshooting-1)
  - [Production Deployment](#production-deployment)
    - [CLI Production Deployment](#cli-production-deployment)
    - [Web Application Production Deployment](#web-application-production-deployment)
      - [Production Checklist](#production-checklist)
      - [Production Architecture](#production-architecture)
      - [Deployment Options](#deployment-options)
      - [Systemd Services](#systemd-services)
      - [Nginx Configuration](#nginx-configuration)
      - [SSL/TLS with Let's Encrypt](#ssltls-with-lets-encrypt)
      - [Monitoring and Maintenance](#monitoring-and-maintenance)
  - [Platform-Specific Instructions](#platform-specific-instructions)
    - [macOS](#macos)
      - [Intel Macs](#intel-macs)
      - [Apple Silicon (M1/M2/M3)](#apple-silicon-m1m2m3)
      - [Common macOS Issues](#common-macos-issues)
    - [Linux (Ubuntu/Debian)](#linux-ubuntudebian)
      - [Prerequisites](#prerequisites)
      - [Installation](#installation)
      - [RHEL/CentOS/Fedora](#rhelcentosfedora)
    - [Windows](#windows)
      - [Prerequisites](#prerequisites-1)
      - [Installation](#installation-1)
      - [WSL2 (Recommended for Windows)](#wsl2-recommended-for-windows)
    - [Docker Deployment](#docker-deployment-1)
      - [Dockerfile](#dockerfile)
      - [Build and Run](#build-and-run)
      - [Docker Compose](#docker-compose)
  - [Troubleshooting](#troubleshooting)
    - [Common Installation Issues](#common-installation-issues)
      - [Issue: `pip: command not found`](#issue-pip-command-not-found)
      - [Issue: `ModuleNotFoundError: No module named 'osmnx'`](#issue-modulenotfounderror-no-module-named-osmnx)
      - [Issue: `ImportError: cannot import name 'packaging' from 'pkg_resources'`](#issue-importerror-cannot-import-name-packaging-from-pkg_resources)
      - [Issue: `ERROR: Could not build wheels for shapely`](#issue-error-could-not-build-wheels-for-shapely)
    - [Runtime Issues](#runtime-issues)
      - [Issue: `ValueError: Could not find coordinates for City, Country`](#issue-valueerror-could-not-find-coordinates-for-city-country)
      - [Issue: `OSMnx timeout or connection errors`](#issue-osmnx-timeout-or-connection-errors)
      - [Issue: `MemoryError` during rendering](#issue-memoryerror-during-rendering)
      - [Issue: Font warnings - "Font not found"](#issue-font-warnings---font-not-found)
    - [Performance Issues](#performance-issues-1)
      - [Slow data fetching (\>60 seconds)](#slow-data-fetching-60-seconds)
      - [High memory usage (\>2GB)](#high-memory-usage-2gb)
  - [Production Deployment](#production-deployment-1)
    - [Server Deployment Recommendations](#server-deployment-recommendations)
      - [1. Use Virtual Environment](#1-use-virtual-environment)
      - [2. Create System Service (Linux)](#2-create-system-service-linux)
      - [3. Implement Logging](#3-implement-logging)
      - [4. Set Up Caching](#4-set-up-caching)
      - [5. Monitoring](#5-monitoring)
  - [Next Steps](#next-steps)
  - [Support](#support)
  - [See Also](#see-also)

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **Operating System** | macOS 10.15+, Linux (Ubuntu 20.04+), Windows 10+ |
| **Python** | 3.9 or higher |
| **Memory (RAM)** | 2 GB minimum, 4 GB recommended |
| **Disk Space** | 500 MB for dependencies, 100 MB per poster |
| **Internet** | Required for OSM data fetching |
| **Network** | Stable connection (50+ Mbps recommended) |

### Python Version Support

| Python Version | Supported | Notes |
|----------------|-----------|-------|
| 3.9 | ✅ Yes | Minimum version |
| 3.10 | ✅ Yes | Recommended |
| 3.11 | ✅ Yes | Recommended |
| 3.12 | ✅ Yes | Latest stable |
| 3.8 | ⚠️ Limited | May work but not tested |
| 3.7 or below | ❌ No | Incompatible dependencies |

### Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| **macOS** (Intel) | ✅ Fully Supported | Native support |
| **macOS** (Apple Silicon) | ✅ Fully Supported | Requires Rosetta for some deps |
| **Linux** (Ubuntu/Debian) | ✅ Fully Supported | Recommended for production |
| **Linux** (RHEL/CentOS) | ✅ Supported | May require additional packages |
| **Windows 10/11** | ✅ Supported | WSL2 recommended for best experience |
| **Docker** | ✅ Supported | See [Docker deployment](#docker-deployment) |

---

## Quick Start

### CLI Quick Start

For users who want to generate posters via command line immediately:

```bash
# Clone or download the repository
git clone <repository-url>
cd maptoposter-web

# Install dependencies
pip install -r requirements.txt

# Generate your first poster
python create_map_poster.py -c "Paris" -C "France" -t noir

# Output will be in posters/ directory
```

### Web Application Quick Start

For users who want to use the web interface:

```bash
# 1. Install dependencies
pip install -r requirements.txt requirements-web.txt

# 2. Start Redis (in separate terminal)
redis-server

# 3. Start Flask web server (in separate terminal)
python run.py

# 4. Start Celery worker (in separate terminal)
python celery_worker.py

# 5. Open browser
open http://localhost:5000
```

### Docker Quick Start

For the fastest and easiest setup:

```bash
# 1. Copy environment file
cp .env.docker .env

# 2. Start all services with Docker Compose
docker-compose up -d

# 3. Access web application
open http://localhost:5000

# 4. View logs
docker-compose logs -f web
```

---

## Installation Methods

### Standard Installation

**Recommended for**: Quick testing, single-user systems

#### Step 1: Verify Python Installation

```bash
python3 --version
# Should show Python 3.9 or higher
```

If Python is not installed:
- **macOS**: `brew install python3`
- **Linux**: `sudo apt install python3 python3-pip`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)

#### Step 2: Download Project

```bash
# Option A: Using git
git clone <repository-url>
cd maptoposter-web

# Option B: Download and extract ZIP
# Then navigate to extracted directory
cd maptoposter-web
```

#### Step 3: Install Dependencies

```bash
pip3 install -r requirements.txt
```

**Expected installation time**: 2-5 minutes depending on internet speed

#### Step 4: Verify Installation

```bash
python3 create_map_poster.py --list-themes
# Should display list of 17 themes
```

---

### Virtual Environment Installation

**Recommended for**: Development, multiple Python projects, production

Virtual environments isolate project dependencies from system Python packages.

#### Using venv (Built-in)

```bash
# Create virtual environment
python3 -m venv env

# Activate virtual environment
# On macOS/Linux:
source env/bin/activate

# On Windows:
env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify
python create_map_poster.py --list-themes

# When done, deactivate
deactivate
```

#### Using virtualenv

```bash
# Install virtualenv if not already installed
pip install virtualenv

# Create virtual environment
virtualenv env

# Activate (same as venv above)
source env/bin/activate  # macOS/Linux
# or
env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

---

### Conda Installation

**Recommended for**: Data science environments, complex dependency management

```bash
# Create conda environment
conda create -n mapgen python=3.11

# Activate environment
conda activate mapgen

# Install dependencies
pip install -r requirements.txt

# Verify
python create_map_poster.py --list-themes

# Deactivate when done
conda deactivate
```

**Alternative**: Install some dependencies via conda for better compatibility:

```bash
conda create -n mapgen python=3.11
conda activate mapgen

# Install heavy dependencies via conda
conda install numpy pandas matplotlib geopandas

# Install remaining via pip
pip install osmnx geopy tqdm
```

---

## Web Application Setup

The City Map Poster Generator now includes a full-featured web application with background job processing, making it accessible through a browser interface.

### Local Development Setup

**Requirements**:
- Python 3.9+
- Redis server
- PostgreSQL (optional, SQLite works for development)

#### Step 1: Install Web Dependencies

```bash
# Install base dependencies
pip install -r requirements.txt

# Install web application dependencies
pip install -r requirements-web.txt
```

**Web dependencies include**:
- `Flask==3.1.0` - Web framework
- `Flask-SQLAlchemy==3.1.1` - Database ORM
- `Flask-Caching==2.3.0` - Caching layer
- `Celery==5.4.0` - Background task processing
- `redis==5.2.1` - Redis client
- `gunicorn==21.2.0` - Production WSGI server

### Redis Installation

Redis is required for caching and Celery task queue.

**macOS**:
```bash
# Install via Homebrew
brew install redis

# Start Redis server
brew services start redis

# Or run in foreground
redis-server
```

**Linux (Ubuntu/Debian)**:
```bash
# Install Redis
sudo apt update
sudo apt install redis-server

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

**Windows**:
```bash
# Option 1: Use WSL2 and install as on Linux

# Option 2: Use Redis for Windows (unofficial)
# Download from: https://github.com/tporadowski/redis/releases

# Option 3: Use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### PostgreSQL Setup (Optional)

PostgreSQL is recommended for production but SQLite works fine for development.

**macOS**:
```bash
# Install via Homebrew
brew install postgresql@16

# Start PostgreSQL
brew services start postgresql@16

# Create database
createdb maptoposter
```

**Linux (Ubuntu/Debian)**:
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE maptoposter;
CREATE USER maptoposter WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE maptoposter TO maptoposter;
EOF
```

### Running the Web Application

You need to run **three processes** simultaneously for the web application:

#### Terminal 1: Flask Web Server

```bash
# Activate virtual environment (if using one)
source env/bin/activate

# Set environment variables (optional)
export FLASK_ENV=development
export FLASK_DEBUG=1

# Start Flask server
python run.py
```

The web application will be available at: **http://localhost:5000**

#### Terminal 2: Celery Worker

```bash
# Activate virtual environment
source env/bin/activate

# Start Celery worker
python celery_worker.py
```

This handles background poster generation tasks.

#### Terminal 3: Redis Server (if not running as service)

```bash
redis-server
```

### Environment Configuration

Create a `.env` file for configuration:

```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
nano .env
```

**Key configuration options**:

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database (SQLite for development)
DATABASE_URL=sqlite:///instance/posters.db

# Or PostgreSQL for production
# DATABASE_URL=postgresql://maptoposter:password@localhost:5432/maptoposter

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# File Storage
POSTER_STORAGE_PATH=posters
THUMBNAIL_STORAGE_PATH=thumbnails
TEMP_STORAGE_PATH=temp
```

### Verify Web Application

1. **Check Flask server**: Open http://localhost:5000 in browser
2. **Check API health**: `curl http://localhost:5000/api/v1/health`
3. **Check Redis**: `redis-cli ping` (should return "PONG")
4. **Check Celery**: Look for "celery@hostname ready" in worker terminal

---

## Docker Deployment

Docker provides the easiest and most reliable way to deploy the web application with all dependencies pre-configured.

### Docker Prerequisites

- **Docker Engine** 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.0+ (included with Docker Desktop)
- **At least 4GB RAM** available
- **10GB disk space** for images and data

Verify installation:
```bash
docker --version
docker-compose --version
```

### Development Mode

Development mode includes hot-reloading and uses SQLite for simplicity.

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start services with development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# 3. Access application
open http://localhost:5000

# 4. View logs
docker-compose logs -f web

# 5. Stop services
docker-compose down
```

**Development features**:
- Source code mounted for hot reloading
- Flask development server (auto-restart on code changes)
- SQLite database (no PostgreSQL needed)
- Debug mode enabled
- Redis port exposed (6379) for debugging

### Production Mode

Production mode uses PostgreSQL, Gunicorn, and proper resource limits.

```bash
# 1. Configure environment
cp .env.docker .env

# Edit .env and set secure values:
# - SECRET_KEY (generate with: python -c 'import secrets; print(secrets.token_hex(32))')
# - POSTGRES_PASSWORD (generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))')
nano .env

# 2. Start services
docker-compose up -d

# 3. Check health
docker-compose ps
curl http://localhost:5000/api/v1/health

# 4. View logs
docker-compose logs -f

# 5. Stop services
docker-compose down
```

**Production features**:
- PostgreSQL database with persistent volume
- Gunicorn WSGI server (4 workers)
- Redis with persistence
- Health checks for all services
- Resource limits (2GB RAM, 2 CPUs per service)
- Auto-restart on failure

### Production with Nginx

For production deployments, add Nginx reverse proxy for SSL/TLS and static file serving.

```bash
# 1. Configure SSL certificates (optional but recommended)
mkdir -p docker/ssl
# Copy your SSL certificates to docker/ssl/

# 2. Start all services including Nginx
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 3. Access via Nginx
# HTTP: http://localhost
# HTTPS: https://localhost (if SSL configured)

# 4. Check Nginx logs
docker-compose logs -f nginx
```

**Nginx provides**:
- SSL/TLS termination
- Static file serving (faster than Flask)
- Gzip compression
- Rate limiting
- Security headers

### Scaling

Scale Celery workers for increased throughput:

```bash
# Scale to 3 Celery workers
docker-compose up -d --scale celery=3

# Check running workers
docker-compose ps celery

# View worker logs
docker-compose logs -f celery
```

**Resource considerations**:
- Each worker uses ~1-2GB RAM during poster generation
- More workers = faster processing but higher memory usage
- Recommended: 1-2 workers per 2GB RAM available

### Docker Management Commands

**Build and deploy**:
```bash
# Build images
docker-compose build

# Build without cache
docker-compose build --no-cache

# Pull latest images
docker-compose pull

# Start services in background
docker-compose up -d

# Restart specific service
docker-compose restart web
```

**Monitoring**:
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f postgres

# Check service status
docker-compose ps

# Check resource usage
docker stats
```

**Database management**:
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U maptoposter -d maptoposter

# Backup database
docker-compose exec postgres pg_dump -U maptoposter maptoposter > backup.sql

# Restore database
docker-compose exec -T postgres psql -U maptoposter maptoposter < backup.sql

# View database logs
docker-compose logs -f postgres
```

**Redis management**:
```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Clear cache
docker-compose exec redis redis-cli FLUSHDB

# Monitor Redis
docker-compose exec redis redis-cli MONITOR

# Check memory usage
docker-compose exec redis redis-cli INFO memory
```

**Celery management**:
```bash
# Check active tasks
docker-compose exec celery celery -A celery_worker.celery inspect active

# Purge all tasks
docker-compose exec celery celery -A celery_worker.celery purge

# Check worker stats
docker-compose exec celery celery -A celery_worker.celery inspect stats
```

**Cleanup**:
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v

# Remove unused images
docker image prune -a

# Full cleanup
docker-compose down -v --remove-orphans
docker image prune -af
docker volume prune -f
```

### Docker Troubleshooting

**Port already in use**:
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "5001:5000"
```

**Database connection failed**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Verify connection from web container
docker-compose exec web python -c "from sqlalchemy import create_engine; import os; engine = create_engine(os.environ['DATABASE_URL']); engine.connect(); print('Connected!')"
```

**Celery not processing tasks**:
```bash
# Check worker logs
docker-compose logs celery

# Restart celery
docker-compose restart celery

# Verify Redis connection
docker-compose exec celery python -c "from redis import Redis; import os; r = Redis.from_url(os.environ['REDIS_URL']); print(r.ping())"
```

**Out of memory**:
```bash
# Check memory usage
docker stats

# Increase memory limits in docker-compose.yml
# Or reduce number of workers

# For development, reduce Celery concurrency
command: celery -A celery_worker.celery worker --concurrency=1
```

**Permission denied**:
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix volume permissions
docker-compose exec web chown -R appuser:appuser /app/posters /app/thumbnails /app/temp
```

See [`DOCKER_README.md`](../DOCKER_README.md) for complete Docker deployment guide.


---

## Dependency Management

### Core Dependencies

The project requires 29 Python packages (see [`requirements.txt`](../requirements.txt)):

**Critical Dependencies** (with version constraints):
- `osmnx==2.0.7` - OpenStreetMap data fetching
- `matplotlib==3.10.8` - Rendering engine
- `geopandas==1.1.2` - Geographic data handling
- `geopy==2.4.1` - Geocoding (Nominatim)
- `numpy==2.4.0` - Numerical operations
- `tqdm==4.67.1` - Progress bars

### Dependency Tree

```
create_map_poster.py
├── osmnx (2.0.7)
│   ├── networkx (3.6.1)
│   ├── geopandas (1.1.2)
│   │   ├── pandas (2.3.3)
│   │   ├── shapely (2.1.2)
│   │   └── pyproj (3.7.2)
│   └── requests (2.32.5)
├── matplotlib (3.10.8)
│   ├── numpy (2.4.0)
│   ├── pillow (12.1.0)
│   └── contourpy (1.3.3)
├── geopy (2.4.1)
└── tqdm (4.67.1)
```

### Version Pinning Strategy

**Current approach**: Exact version pinning for reproducibility

```
osmnx==2.0.7    # Exact version (recommended for production)
```

**Alternative approaches**:

```
osmnx>=2.0.0,<3.0.0   # Major version constraint
osmnx~=2.0.7          # Compatible release
```

### Updating Dependencies

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade osmnx

# Update all packages (CAUTION: may break compatibility)
pip install --upgrade -r requirements.txt

# Freeze updated versions
pip freeze > requirements.txt
```

---

## Configuration

### Directory Structure

After installation, ensure the following directories exist:

```
maptoposter-web/
├── create_map_poster.py    # Main script
├── requirements.txt        # Dependencies
├── README.md              # Basic documentation
├── docs/                  # Comprehensive documentation
├── themes/                # Theme JSON files (17 themes)
│   ├── noir.json
│   ├── blueprint.json
│   └── ... (15 more)
├── fonts/                 # Roboto font files (3 files)
│   ├── Roboto-Bold.ttf
│   ├── Roboto-Regular.ttf
│   └── Roboto-Light.ttf
└── posters/              # Output directory (auto-created)
```

**Auto-created directories**:
- `posters/` - Created on first run if missing
- `themes/` - Created if missing (but needed for themes)

### Configuration Constants

Located in [`create_map_poster.py`](../create_map_poster.py:14-16):

```python
THEMES_DIR = "themes"      # Theme JSON directory
FONTS_DIR = "fonts"        # Font files directory
POSTERS_DIR = "posters"    # Output directory
```

**To customize locations**, modify these constants before first run.

### Environment Variables

**Optional environment variables** for advanced configuration:

```bash
# Nominatim API configuration
export NOMINATIM_USER_AGENT="my_custom_app_name"

# HTTP request timeout (seconds)
export NOMINATIM_TIMEOUT=10

# OSMnx cache directory
export OSMNX_CACHE_DIR="./cache/osmnx"
```

---

## Verification

### Post-Installation Checks

Run these commands to verify correct installation:

#### 1. Check Python Version

```bash
python3 --version
# Expected: Python 3.9.x or higher
```

#### 2. Verify Dependencies

```bash
python3 -c "import osmnx; print(f'OSMnx version: {osmnx.__version__}')"
# Expected: OSMnx version: 2.0.7

python3 -c "import matplotlib; print(f'Matplotlib version: {matplotlib.__version__}')"
# Expected: Matplotlib version: 3.10.8
```

#### 3. Check File Structure

```bash
ls -la themes/
# Should list 17 .json files

ls -la fonts/
# Should list 3 .ttf files
```

#### 4. List Available Themes

```bash
python3 create_map_poster.py --list-themes
# Should display 17 themes with descriptions
```

#### 5. Test Run (Quick)

```bash
# Generate small test poster (Venice - small area)
python3 create_map_poster.py -c "Venice" -C "Italy" -t blueprint -d 4000

# Check output
ls -lh posters/venice_blueprint_*.png
# Should show ~5-15 MB PNG file
```

### Health Check Script

Create a simple health check script:

```python
#!/usr/bin/env python3
# health_check.py

import sys

def check_imports():
    """Verify all required imports"""
    try:
        import osmnx
        import matplotlib
        import geopandas
        import geopy
        import tqdm
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def check_directories():
    """Verify directory structure"""
    import os
    dirs = ['themes', 'fonts']
    for d in dirs:
        if os.path.exists(d):
            print(f"✅ {d}/ directory found")
        else:
            print(f"❌ {d}/ directory missing")
            return False
    return True

def check_themes():
    """Verify theme files"""
    import os
    import json
    
    theme_count = len([f for f in os.listdir('themes') if f.endswith('.json')])
    if theme_count > 0:
        print(f"✅ Found {theme_count} theme files")
        return True
    else:
        print("❌ No theme files found")
        return False

if __name__ == "__main__":
    checks = [
        check_imports(),
        check_directories(),
        check_themes()
    ]
    
    if all(checks):
        print("\n✅ All checks passed! Ready to generate posters.")
        sys.exit(0)
    else:

### Web Application Troubleshooting

#### Redis Connection Error

**Symptoms**: "Connection refused" or "Redis not available" errors

**Solutions**:
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running, start Redis
# macOS:
brew services start redis
# Linux:
sudo systemctl start redis-server
# Manual:
redis-server

# Check Redis URL in .env
cat .env | grep REDIS_URL
# Should be: redis://localhost:6379/0
```

#### Celery Worker Not Starting

**Symptoms**: Tasks stuck in "pending" status

**Solutions**:
```bash
# Check if Celery worker is running
ps aux | grep celery_worker

# Start worker with verbose logging
python celery_worker.py --loglevel=debug

# Check for import errors
python -c "from app import create_app; app = create_app(); print('OK')"

# Verify Celery can connect to Redis
python -c "from redis import Redis; r = Redis.from_url('redis://localhost:6379/1'); print(r.ping())"
```

#### Database Errors

**SQLite locked error**:
```bash
# SQLite doesn't handle concurrent writes well
# Solution: Use PostgreSQL for production or reduce concurrency

# Quick fix for development: restart services
pkill -f celery_worker
python run.py &
python celery_worker.py &
```

**PostgreSQL connection error**:
```bash
# Check PostgreSQL is running
pg_isready

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"

# Check if database exists
psql -U postgres -l | grep maptoposter
```

#### Import Errors

**"No module named 'app'" or similar**:
```bash
# Ensure you're in the project root directory
pwd
# Should show: /path/to/maptoposter-web

# Ensure virtual environment is activated
which python
# Should show: /path/to/maptoposter-web/env/bin/python

# Reinstall web dependencies
pip install -r requirements-web.txt

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

#### Port Already in Use

**Error**: "Address already in use" on port 5000

**Solutions**:
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use different port
FLASK_PORT=5001 python run.py
```

#### Tasks Failing

**Check task logs**:
```bash
# View Celery worker output
docker-compose logs -f celery  # Docker
# Or check terminal running celery_worker.py

# Check job status in database
python -c "
from app import create_app
from app.models import Job
app = create_app()
with app.app_context():
    jobs = Job.query.filter_by(status='failed').all()
    for job in jobs:
        print(f'{job.id}: {job.error_message}')
"
```

#### Performance Issues

**Slow poster generation**:
```bash
# Check Redis cache hit rate
redis-cli INFO stats | grep cache

# Enable geocoding cache
# Already enabled by default, but verify in app/services/geocoding_service.py

# Use smaller distance for testing
# distance=12000 instead of 29000

# Check system resources
top
df -h
```

### Docker Troubleshooting

See the [Docker Deployment](#docker-deployment) section and [`DOCKER_README.md`](../DOCKER_README.md) for comprehensive Docker troubleshooting.

---

## Production Deployment

### CLI Production Deployment

For running CLI tool as a service or batch processing, see [Server Deployment Recommendations](#server-deployment-recommendations) above.

### Web Application Production Deployment

#### Production Checklist

Before deploying to production, ensure:

- [ ] **Security**
  - [ ] Strong `SECRET_KEY` generated
  - [ ] Strong database passwords
  - [ ] `.env` file not committed to version control
  - [ ] SSL/TLS certificates configured
  - [ ] Firewall rules configured
  - [ ] Rate limiting enabled

- [ ] **Database**
  - [ ] PostgreSQL configured (not SQLite)
  - [ ] Database backups scheduled
  - [ ] Connection pooling configured
  - [ ] Migrations applied

- [ ] **Caching**
  - [ ] Redis persistence enabled
  - [ ] Cache expiration configured
  - [ ] Memory limits set

- [ ] **Monitoring**
  - [ ] Application logs configured
  - [ ] Error tracking setup (e.g., Sentry)
  - [ ] Resource monitoring (CPU, RAM, disk)
  - [ ] Health check endpoints working

- [ ] **Performance**
  - [ ] Gunicorn workers configured (4-8 workers)
  - [ ] Celery workers scaled appropriately
  - [ ] Static files served by Nginx
  - [ ] Gzip compression enabled

- [ ] **Backup**
  - [ ] Database backup strategy
  - [ ] Poster files backup
  - [ ] Configuration backup

#### Production Architecture

Recommended production setup:

```
Internet
    ↓
[Nginx] (SSL/TLS, static files, rate limiting)
    ↓
[Gunicorn] (4-8 workers)
    ↓
[Flask App] ← → [Redis] (cache + message broker)
    ↓              ↓
[PostgreSQL]  [Celery Workers] (2-4 workers)
    ↓
[Persistent Storage] (posters, thumbnails)
```

#### Deployment Options

**Option 1: Docker (Recommended)**

Easiest and most reliable:

```bash
# Use docker-compose.prod.yml
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitor services
docker-compose ps
docker-compose logs -f
```

See [`DOCKER_README.md`](../DOCKER_README.md) for complete guide.

**Option 2: Manual Server Setup**

For custom server configurations:

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv
sudo apt install redis-server postgresql nginx
sudo apt install libgeos-dev libproj-dev

# 2. Create application user
sudo useradd -m -s /bin/bash maptoposter

# 3. Setup application directory
sudo mkdir -p /opt/maptoposter
sudo chown maptoposter:maptoposter /opt/maptoposter

# 4. Deploy application
sudo -u maptoposter bash << 'EOF'
cd /opt/maptoposter
git clone <repo-url> .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt requirements-web.txt gunicorn
EOF

# 5. Configure database
sudo -u postgres psql << EOF
CREATE DATABASE maptoposter;
CREATE USER maptoposter WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE maptoposter TO maptoposter;
EOF

# 6. Configure environment
sudo -u maptoposter bash << 'EOF'
cd /opt/maptoposter
cp .env.example .env
# Edit .env with production settings
nano .env
EOF

# 7. Setup systemd services (see below)
```

#### Systemd Services

**Flask Web Service** (`/etc/systemd/system/maptoposter-web.service`):

```ini
[Unit]
Description=City Map Poster Generator Web Application
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=notify
User=maptoposter
Group=maptoposter
WorkingDirectory=/opt/maptoposter
Environment="PATH=/opt/maptoposter/venv/bin"
EnvironmentFile=/opt/maptoposter/.env
ExecStart=/opt/maptoposter/venv/bin/gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 4 \
    --timeout 300 \
    --access-logfile /var/log/maptoposter/access.log \
    --error-logfile /var/log/maptoposter/error.log \
    run:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Celery Worker Service** (`/etc/systemd/system/maptoposter-celery.service`):

```ini
[Unit]
Description=City Map Poster Generator Celery Worker
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=maptoposter
Group=maptoposter
WorkingDirectory=/opt/maptoposter
Environment="PATH=/opt/maptoposter/venv/bin"
EnvironmentFile=/opt/maptoposter/.env
ExecStart=/opt/maptoposter/venv/bin/celery \
    -A celery_worker.celery worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=50 \
    --logfile=/var/log/maptoposter/celery.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start services**:

```bash
# Create log directory
sudo mkdir -p /var/log/maptoposter
sudo chown maptoposter:maptoposter /var/log/maptoposter

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable maptoposter-web
sudo systemctl enable maptoposter-celery

# Start services
sudo systemctl start maptoposter-web
sudo systemctl start maptoposter-celery

# Check status
sudo systemctl status maptoposter-web
sudo systemctl status maptoposter-celery

# View logs
sudo journalctl -u maptoposter-web -f
sudo journalctl -u maptoposter-celery -f
```

#### Nginx Configuration

Create `/etc/nginx/sites-available/maptoposter`:

```nginx
upstream maptoposter {
    server 127.0.0.1:5000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logging
    access_log /var/log/nginx/maptoposter_access.log;
    error_log /var/log/nginx/maptoposter_error.log;
    
    # Max upload size
    client_max_body_size 10M;
    
    # Static files
    location /static/ {
        alias /opt/maptoposter/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Generated posters
    location /posters/ {
        alias /opt/maptoposter/posters/;
        expires 30d;
        add_header Cache-Control "public";
    }
    
    # Proxy to Flask application
    location / {
        proxy_pass http://maptoposter;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Rate limiting for API
    location /api/ {
        limit_req zone=api_limit burst=10 nodelay;
        proxy_pass http://maptoposter;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Rate limit zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
```

**Enable Nginx configuration**:

```bash
# Test configuration
sudo nginx -t

# Enable site
sudo ln -s /etc/nginx/sites-available/maptoposter /etc/nginx/sites-enabled/

# Reload Nginx
sudo systemctl reload nginx
```

#### SSL/TLS with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

#### Monitoring and Maintenance

**Setup monitoring**:

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Setup log rotation
sudo nano /etc/logrotate.d/maptoposter
```

Add to `/etc/logrotate.d/maptoposter`:

```
/var/log/maptoposter/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 maptoposter maptoposter
    sharedscripts
    postrotate
        systemctl reload maptoposter-web
        systemctl reload maptoposter-celery
    endscript
}
```

**Backup strategy**:

```bash
# Create backup script
sudo nano /opt/maptoposter/backup.sh
```

Add to `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/maptoposter/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
pg_dump -U maptoposter maptoposter > "$BACKUP_DIR/database.sql"

# Backup posters
tar czf "$BACKUP_DIR/posters.tar.gz" /opt/maptoposter/posters/

# Backup configuration
cp /opt/maptoposter/.env "$BACKUP_DIR/env"

echo "Backup completed: $BACKUP_DIR"
```

```bash
# Make executable
chmod +x /opt/maptoposter/backup.sh

# Add to crontab (daily backup at 2 AM)
sudo crontab -e
# Add: 0 2 * * * /opt/maptoposter/backup.sh
```

**Health monitoring**:

```bash
# Setup monitoring script
sudo nano /opt/maptoposter/healthcheck.sh
```

Add to `healthcheck.sh`:

```bash
#!/bin/bash
HEALTH_URL="http://localhost:5000/api/v1/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$RESPONSE" != "200" ]; then
    echo "Health check failed: HTTP $RESPONSE"
    # Send alert (email, Slack, etc.)
    # Optionally restart services
    # systemctl restart maptoposter-web
    exit 1
fi

echo "Health check passed"
exit 0
```

```bash
# Make executable
chmod +x /opt/maptoposter/healthcheck.sh

# Run every 5 minutes via cron
# */5 * * * * /opt/maptoposter/healthcheck.sh
```

        print("\n❌ Some checks failed. Please review installation.")
        sys.exit(1)
```

Run it:
```bash
python3 health_check.py
```

---

## Platform-Specific Instructions

### macOS

#### Intel Macs

Standard installation works without issues:

```bash
pip3 install -r requirements.txt
```

#### Apple Silicon (M1/M2/M3)

Some dependencies may need special handling:

```bash
# Option 1: Use Rosetta
arch -x86_64 pip3 install -r requirements.txt

# Option 2: Install native ARM versions
pip3 install -r requirements.txt
# Most packages now have ARM64 wheels
```

**If you encounter issues with specific packages**:

```bash
# Install via conda (better ARM support)
conda install -c conda-forge geopandas osmnx matplotlib
pip install geopy tqdm
```

#### Common macOS Issues

**Issue**: "xcrun: error: invalid active developer path"
```bash
# Solution: Install Xcode Command Line Tools
xcode-select --install
```

**Issue**: Font rendering warnings
```bash
# Solution: Clear matplotlib cache
rm -rf ~/.matplotlib/
```

---

### Linux (Ubuntu/Debian)

#### Prerequisites

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip

# Install system dependencies for spatial libraries
sudo apt install python3-dev build-essential libgeos-dev libproj-dev
```

#### Installation

```bash
# Upgrade pip
pip3 install --upgrade pip

# Install dependencies
pip3 install -r requirements.txt
```

#### RHEL/CentOS/Fedora

```bash
# Install Python and development tools
sudo dnf install python3 python3-pip python3-devel gcc gcc-c++ make

# Install GEOS and PROJ
sudo dnf install geos geos-devel proj proj-devel

# Install dependencies
pip3 install -r requirements.txt
```

---

### Windows

#### Prerequisites

1. **Install Python** from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation

2. **Install Microsoft Visual C++ Build Tools** (for some dependencies)
   - Download from [Visual Studio Downloads](https://visualstudio.microsoft.com/downloads/)
   - Or install via `pip install wheel`

#### Installation

**Using Command Prompt**:

```cmd
# Navigate to project directory
cd path\to\maptoposter-web

# Install dependencies
pip install -r requirements.txt

# Run script
python create_map_poster.py --list-themes
```

**Using PowerShell**:

```powershell
# Same commands as Command Prompt
pip install -r requirements.txt
python create_map_poster.py -c "Paris" -C "France" -t noir
```

#### WSL2 (Recommended for Windows)

Windows Subsystem for Linux provides better compatibility:

```bash
# In WSL2 Ubuntu terminal
sudo apt update
sudo apt install python3 python3-pip
pip3 install -r requirements.txt
```

**Benefits of WSL2**:
- Better package compatibility
- Faster file I/O
- Native Linux environment

---

### Docker Deployment

#### Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create output directory
RUN mkdir -p posters

# Set entrypoint
ENTRYPOINT ["python", "create_map_poster.py"]
CMD ["--list-themes"]
```

#### Build and Run

```bash
# Build image
docker build -t mapgen .

# Run (list themes)
docker run mapgen --list-themes

# Generate poster
docker run -v $(pwd)/posters:/app/posters mapgen \
  -c "Tokyo" -C "Japan" -t japanese_ink

# Output will be in ./posters/
```

#### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mapgen:
    build: .
    volumes:
      - ./posters:/app/posters
      - ./themes:/app/themes
    environment:
      - NOMINATIM_USER_AGENT=map_poster_docker
```

Run:
```bash
docker-compose run mapgen -c "Paris" -C "France" -t noir
```

---

## Troubleshooting

### Common Installation Issues

#### Issue: `pip: command not found`

**Solution**:
```bash
# macOS/Linux
python3 -m ensurepip --upgrade

# Or install pip manually
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

---

#### Issue: `ModuleNotFoundError: No module named 'osmnx'`

**Cause**: Dependencies not installed or wrong Python interpreter

**Solution**:
```bash
# Ensure you're using the correct Python
which python3
python3 --version

# Reinstall dependencies
pip3 install -r requirements.txt

# Or explicitly use python3 -m pip
python3 -m pip install -r requirements.txt
```

---

#### Issue: `ImportError: cannot import name 'packaging' from 'pkg_resources'`

**Cause**: Outdated setuptools/pip

**Solution**:
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

#### Issue: `ERROR: Could not build wheels for shapely`

**Cause**: Missing system dependencies (GEOS library)

**Solution**:

**macOS**:
```bash
brew install geos
pip install shapely
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt install libgeos-dev
pip install shapely
```

**Windows**:
```bash
# Use pre-built wheel
pip install --upgrade pip
pip install shapely  # Will download pre-built wheel
```

---

### Runtime Issues

#### Issue: `ValueError: Could not find coordinates for City, Country`

**Causes & Solutions**:

1. **Typo in city/country name**
   ```bash
   # Wrong
   python create_map_poster.py -c "Pari" -C "France"
   
   # Correct
   python create_map_poster.py -c "Paris" -C "France"
   ```

2. **Need more specific location**
   ```bash
   # Ambiguous
   python create_map_poster.py -c "Springfield" -C "USA"
   
   # Specific
   python create_map_poster.py -c "Springfield" -C "Illinois, USA"
   ```

3. **Network connectivity issue**
   ```bash
   # Test internet connection
   ping nominatim.openstreetmap.org
   
   # Check firewall settings
   ```

---

#### Issue: `OSMnx timeout or connection errors`

**Cause**: Network issues or API rate limiting

**Solution**:
```bash
# Wait 1-2 minutes and retry
# OSMnx has built-in retry logic

# For persistent issues, check Overpass API status:
# https://overpass-api.de/api/status

# Try again with smaller distance
python create_map_poster.py -c "City" -C "Country" -d 10000  # Reduce from 29000
```

---

#### Issue: `MemoryError` during rendering

**Cause**: Large city + high distance value

**Solution**:
```bash
# Reduce distance parameter
python create_map_poster.py -c "Mumbai" -C "India" -d 12000  # Instead of 29000

# Or increase system memory (if possible)
```

---

#### Issue: Font warnings - "Font not found"

**Cause**: Missing Roboto font files

**Solution**:
```bash
# Check fonts directory
ls fonts/
# Should show: Roboto-Bold.ttf, Roboto-Regular.ttf, Roboto-Light.ttf

# Script will fallback to system monospace fonts if missing
# To fix, download Roboto fonts and place in fonts/ directory
```

---

### Performance Issues

#### Slow data fetching (>60 seconds)

**Causes**:
- Large distance parameter (>20km)
- Slow internet connection
- Complex city (dense street network)

**Solutions**:
```bash
# 1. Reduce distance
python create_map_poster.py -c "Tokyo" -C "Japan" -d 12000  # Instead of 29000

# 2. Implement caching (future enhancement)
# 3. Use faster network connection
```

#### High memory usage (>2GB)

**Cause**: Large/complex city rendering

**Solutions**:
```bash
# 1. Close other applications
# 2. Reduce distance parameter
# 3. Use network_type='drive' (requires code modification)
```

---

## Production Deployment

### Server Deployment Recommendations

For running as a service or batch processing:

#### 1. Use Virtual Environment

```bash
# Create production environment
python3 -m venv /opt/mapgen/env
source /opt/mapgen/env/bin/activate
pip install -r requirements.txt
```

#### 2. Create System Service (Linux)

Create `/etc/systemd/system/mapgen.service`:

```ini
[Unit]
Description=Map Poster Generator Service
After=network.target

[Service]
Type=oneshot
User=mapgen
WorkingDirectory=/opt/mapgen
Environment="PATH=/opt/mapgen/env/bin"
ExecStart=/opt/mapgen/env/bin/python create_map_poster.py -c "Paris" -C "France"

[Install]
WantedBy=multi-user.target
```

Enable and run:
```bash
sudo systemctl enable mapgen.service
sudo systemctl start mapgen.service
```

#### 3. Implement Logging

Modify script to log to file:
```python
import logging

logging.basicConfig(
    filename='/var/log/mapgen.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

#### 4. Set Up Caching

Add caching layer to reduce API calls:
```python
import sqlite3
import json

def get_cached_coordinates(city, country):
    conn = sqlite3.connect('cache/geocode.db')
    cursor = conn.cursor()
    cursor.execute("SELECT lat, lon FROM geocache WHERE city=? AND country=?", (city, country))
    result = cursor.fetchone()
    conn.close()
    return result if result else None
```

#### 5. Monitoring

Use system monitoring tools:
```bash
# Monitor process
watch -n 5 'ps aux | grep create_map_poster'

# Monitor memory
watch -n 5 'free -h'

# Monitor disk usage
watch -n 30 'du -sh posters/'
```

---

## Next Steps

After successful installation:

1. **Read the documentation**:
   - [Technical Overview](TECHNICAL_OVERVIEW.md) - Understand architecture
   - [API Reference](API_REFERENCE.md) - Function documentation
   - [Theme System](THEME_SYSTEM.md) - Create custom themes

2. **Generate your first poster**:
   ```bash
   python create_map_poster.py -c "Your City" -C "Your Country" -t noir
   ```

3. **Explore themes**:
   ```bash
   python create_map_poster.py --list-themes
   ```

4. **Customize and extend**: See [FUTURE_AGENTS.md](FUTURE_AGENTS.md) for development guide

---

## Support

For additional help:

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive guides in `docs/` directory
- **Community**: Contribute improvements and share your posters

---

## See Also

**CLI Documentation**:
- [Technical Overview](TECHNICAL_OVERVIEW.md) - CLI system architecture
- [API Reference](API_REFERENCE.md) - CLI function documentation
- [Theme System](THEME_SYSTEM.md) - Theme creation guide
- [Future Agents Guide](FUTURE_AGENTS.md) - Development reference

**Web Application Documentation**:
- [Web Architecture](WEB_ARCHITECTURE.md) - Web application design
- [Web README](../WEB_README.md) - Web application quick start
- [Docker README](../DOCKER_README.md) - Docker deployment guide

**Related Resources**:
- [Main README](../README.md) - Project overview
- [.env.example](../.env.example) - Configuration reference