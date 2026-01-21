# Docker Deployment Guide

Complete guide for deploying the City Map Poster Generator using Docker and Docker Compose.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Modes](#deployment-modes)
- [Configuration](#configuration)
- [Service Architecture](#service-architecture)
- [Management](#management)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Production Checklist](#production-checklist)
- [Advanced Topics](#advanced-topics)

---

## Overview

Docker deployment provides a complete, isolated environment with all dependencies pre-configured. This is the recommended deployment method for both development and production.

### Why Docker?

- ✅ **Consistent environment** across development and production
- ✅ **All dependencies included** (Python, PostgreSQL, Redis, Nginx)
- ✅ **Easy scaling** with Docker Compose
- ✅ **Isolated** from host system
- ✅ **Simple updates** via container rebuilds
- ✅ **Production-ready** with health checks and resource limits

### What's Included

The Docker setup includes:
- **Web application** (Flask + Gunicorn)
- **PostgreSQL** database with persistent storage
- **Redis** for caching and message broker
- **Celery workers** for background job processing
- **Nginx** reverse proxy (optional, production only)

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| **Docker Engine** | 20.10+ | 24.0+ |
| **Docker Compose** | 2.0+ | 2.20+ |
| **RAM** | 4 GB | 8 GB |
| **Disk Space** | 10 GB | 20 GB |
| **CPU Cores** | 2 | 4 |

### Install Docker

**macOS**:
```bash
# Install Docker Desktop
brew install --cask docker

# Or download from https://www.docker.com/products/docker-desktop
```

**Linux (Ubuntu/Debian)**:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**Windows**:
- Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
- Enable WSL2 backend for better performance

### Verify Installation

```bash
docker --version
# Docker version 24.0.0 or higher

docker-compose --version  
# Docker Compose version 2.20.0 or higher

docker run hello-world
# Should download and run successfully
```

---

## Quick Start

### Development Mode (SQLite)

Fastest way to start for development:

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start services with development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# 3. Access application
open http://localhost:5000

# 4. View logs (in separate terminal)
docker-compose logs -f web celery

# 5. Stop services
docker-compose down
```

### Production Mode (PostgreSQL)

For production deployment:

```bash
# 1. Configure environment
cp .env.docker .env

# Edit .env and set:
# - SECRET_KEY (generate with: python -c 'import secrets; print(secrets.token_hex(32))')
# - POSTGRES_PASSWORD (strong password)
nano .env

# 2. Start all services
docker-compose up -d

# 3. Check health
docker-compose ps
curl http://localhost:5000/api/v1/health

# 4. View logs
docker-compose logs -f

# 5. Stop services
docker-compose down
```

### Production with Nginx

For production with SSL/TLS:

```bash
# 1. Configure SSL certificates (if available)
mkdir -p docker/ssl
# Copy certificates to docker/ssl/

# 2. Start with Nginx
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 3. Access via Nginx
curl http://localhost/api/v1/health

# For HTTPS (after SSL configuration):
curl https://yourdomain.com/api/v1/health
```

---

## Deployment Modes

### Development Mode

**File**: [`docker-compose.dev.yml`](../docker-compose.dev.yml)

**Features**:
- Source code mounted for hot reloading
- Flask development server (auto-restart)
- SQLite database (simpler setup)
- Debug mode enabled
- Redis port exposed (6379) for debugging

**Command**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**When to use**: Local development, testing

---

### Production Mode (Basic)

**File**: [`docker-compose.yml`](../docker-compose.yml)

**Features**:
- PostgreSQL database with persistence
- Gunicorn WSGI server (4 workers)
- Resource limits (2GB RAM, 2 CPUs)
- Health checks for all services
- Auto-restart on failure

**Command**:
```bash
docker-compose up -d
```

**When to use**: Production deployment without Nginx

---

### Production Mode (with Nginx)

**Files**: [`docker-compose.yml`](../docker-compose.yml) + [`docker-compose.prod.yml`](../docker-compose.prod.yml)

**Features**:
- All features from basic production mode
- Nginx reverse proxy
- SSL/TLS support
- Static file serving
- Rate limiting
- Gzip compression

**Command**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**When to use**: Production with custom domain and SSL

---

## Configuration

### Environment Variables

Create `.env` file from template:

```bash
cp .env.docker .env
nano .env
```

**Critical variables**:

```bash
# Flask
FLASK_ENV=production
SECRET_KEY=<generate-with: python -c 'import secrets; print(secrets.token_hex(32))'>

# PostgreSQL
POSTGRES_PASSWORD=<strong-password>
DATABASE_URL=postgresql://maptoposter:<password>@postgres:5432/maptoposter

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Storage
POSTER_STORAGE_PATH=/app/posters
THUMBNAIL_STORAGE_PATH=/app/thumbnails
TEMP_STORAGE_PATH=/app/temp
```

### Generate Secure Keys

```bash
# Generate SECRET_KEY
python -c 'import secrets; print(secrets.token_hex(32))'

# Generate database password
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

### Docker Compose Configuration

**Base configuration**: [`docker-compose.yml`](../docker-compose.yml)
- Defines core services (web, celery, postgres, redis)
- Production-ready defaults
- Resource limits and health checks

**Development overrides**: [`docker-compose.dev.yml`](../docker-compose.dev.yml)
- Mounts source code for live editing
- Uses SQLite instead of PostgreSQL
- Exposes additional ports

**Production overrides**: [`docker-compose.prod.yml`](../docker-compose.prod.yml)
- Adds Nginx service
- SSL/TLS configuration
- Production-optimized settings

---

## Service Architecture

### Service Overview

```
┌─────────────────────────────────────────────────────┐
│                    Nginx (optional)                  │
│  Port 80/443 → Reverse Proxy + SSL/TLS             │
└────────────────────┬────────────────────────────────┘
                     │
          ┌──────────┴─────────────┐
          │                        │
          ▼                        │
┌─────────────────────┐            │
│   Flask Web App     │            │
│   Port 5000         │            │
│   Gunicorn (4 workers)│          │
└──────────┬──────────┘            │
           │                       │
           ├───────────────────────┤
           │                       │
           ▼                       ▼
    ┌────────────┐         ┌──────────────┐
    │ PostgreSQL │         │    Redis     │
    │  Port 5432 │         │  Port 6379   │
    │            │         │  - Cache     │
    │            │         │  - Broker    │
    └────────────┘         └──────┬───────┘
                                  │
                                  ▼
                          ┌──────────────┐
                          │Celery Worker │
                          │(2-4 workers) │
                          │- Poster gen  │
                          └──────────────┘
```

### Services Details

#### Web Service

**Image**: Built from [`Dockerfile`](../Dockerfile)  
**Ports**: 5000 (internal), exposed as configured  
**Command**: `gunicorn --bind 0.0.0.0:5000 --workers 4 run:app`  
**Resources**: 1-2 CPUs, 1-2GB RAM  
**Health Check**: `curl http://localhost:5000/api/v1/health`

**Dependencies**: postgres, redis

---

#### Celery Service

**Image**: Same as web service  
**Command**: `celery -A celery_worker.celery worker --loglevel=info --concurrency=2`  
**Resources**: 1-2 CPUs, 1.5-3GB RAM  
**Health Check**: None (monitoring via logs)

**Dependencies**: postgres, redis

---

#### PostgreSQL Service

**Image**: `postgres:16-alpine`  
**Port**: 5432 (internal only)  
**Volume**: `postgres_data` → `/var/lib/postgresql/data`  
**Health Check**: `pg_isready -U maptoposter`

---

#### Redis Service

**Image**: `redis:7-alpine`  
**Port**: 6379 (internal only, exposed in dev mode)  
**Volume**: `redis_data` → `/data`  
**Command**: `redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru`  
**Health Check**: `redis-cli ping`

---

#### Nginx Service (Production Only)

**Image**: `nginx:1.25-alpine`  
**Ports**: 80 (HTTP), 443 (HTTPS)  
**Config**: [`docker/nginx.conf`](../docker/nginx.conf)  
**Volumes**: 
- Static files
- SSL certificates
- Generated posters

---

## Management

### Starting Services

```bash
# Start all services (detached)
docker-compose up -d

# Start specific service
docker-compose up -d web

# Start with logs
docker-compose up

# Start with rebuilt images
docker-compose up -d --build
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v

# Stop specific service
docker-compose stop web
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 web

# Since timestamp
docker-compose logs --since 2024-01-19T10:00:00 web
```

### Service Status

```bash
# Check all services
docker-compose ps

# Detailed status
docker-compose ps -a

# Resource usage
docker stats
```

### Scaling Services

```bash
# Scale Celery workers
docker-compose up -d --scale celery=3

# Verify scaling
docker-compose ps celery

# Scale back
docker-compose up -d --scale celery=1
```

### Executing Commands

```bash
# Access web container shell
docker-compose exec web /bin/bash

# Run Python command
docker-compose exec web python -c "print('Hello')"

# Access PostgreSQL
docker-compose exec postgres psql -U maptoposter -d maptoposter

# Access Redis CLI
docker-compose exec redis redis-cli

# Run as root (for debugging)
docker-compose exec -u root web /bin/bash
```

### Database Management

```bash
# Backup database
docker-compose exec postgres pg_dump -U maptoposter maptoposter > backup.sql

# Restore database
docker-compose exec -T postgres psql -U maptoposter maptoposter < backup.sql

# Access database shell
docker-compose exec postgres psql -U maptoposter -d maptoposter

# View tables
docker-compose exec postgres psql -U maptoposter -d maptoposter -c "\dt"

# Check database size
docker-compose exec postgres psql -U maptoposter -d maptoposter -c "\l+"
```

### Redis Management

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Clear cache
docker-compose exec redis redis-cli FLUSHDB

# Monitor commands
docker-compose exec redis redis-cli MONITOR

# Get memory info
docker-compose exec redis redis-cli INFO memory

# Get key count
docker-compose exec redis redis-cli DBSIZE
```

### Celery Management

```bash
# Check active tasks
docker-compose exec celery celery -A celery_worker.celery inspect active

# Check registered tasks
docker-compose exec celery celery -A celery_worker.celery inspect registered

# Purge all tasks
docker-compose exec celery celery -A celery_worker.celery purge

# Check worker stats
docker-compose exec celery celery -A celery_worker.celery inspect stats
```

---

## Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:5000/api/v1/health | jq

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping

# Nginx health (if using)
curl http://localhost/api/v1/health
```

### Resource Monitoring

```bash
# Real-time stats
docker stats

# Resource usage by service
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Disk usage
docker system df

# Volume usage
docker volume ls
du -sh $(docker volume inspect postgres_data --format '{{.Mountpoint}}')
```

### Log Monitoring

```bash
# Tail all logs
docker-compose logs -f

# Filter by service
docker-compose logs -f web celery

# Search logs
docker-compose logs web | grep ERROR

# Export logs
docker-compose logs --no-color > logs.txt
```

---

## Troubleshooting

### Common Issues

#### Port Already in Use

**Error**: "Bind for 0.0.0.0:5000 failed: port is already allocated"

**Solution**:
```bash
# Find process using port
lsof -i :5000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "5001:5000"
```

---

#### Database Connection Failed

**Error**: "could not connect to server: Connection refused"

**Diagnosis**:
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL health
docker-compose exec postgres pg_isready
```

**Solution**:
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Or rebuild if persistent
docker-compose up -d --build postgres
```

---

#### Celery Not Processing Tasks

**Symptoms**: Tasks stuck in "pending" status

**Diagnosis**:
```bash
# Check Celery logs
docker-compose logs celery

# Check Redis connection
docker-compose exec celery python -c "from redis import Redis; import os; r = Redis.from_url(os.environ['REDIS_URL']); print(r.ping())"

# Check for active workers
docker-compose exec celery celery -A celery_worker.celery inspect active
```

**Solution**:
```bash
# Restart Celery worker
docker-compose restart celery

# Or rebuild
docker-compose up -d --build celery
```

---

#### Out of Memory

**Symptoms**: Services being killed, OOM errors in logs

**Diagnosis**:
```bash
# Check memory usage
docker stats

# Check system memory
free -h
```

**Solution**:
```bash
# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → Increase to 8GB

# Or reduce Celery concurrency
# In docker-compose.yml:
command: celery -A celery_worker.celery worker --concurrency=1

# Restart services
docker-compose restart
```

---

#### Volume Permission Errors

**Error**: "Permission denied" when accessing volumes

**Solution**:
```bash
# Fix permissions
docker-compose exec web chown -R appuser:appuser /app/posters /app/thumbnails

# Or rebuild with correct permissions
docker-compose down
docker-compose up -d --build
```

---

## Production Checklist

Before deploying to production:

- [ ] **Security**
  - [ ] Strong `SECRET_KEY` generated
  - [ ] Strong `POSTGRES_PASSWORD` set
  - [ ] `.env` file not in version control
  - [ ] SSL/TLS certificates configured
  - [ ] Firewall rules configured

- [ ] **Configuration**
  - [ ] `FLASK_ENV=production` set
  - [ ] Database URL points to PostgreSQL
  - [ ] Redis persistence enabled
  - [ ] Resource limits configured

- [ ] **Backups**
  - [ ] Database backup strategy in place
  - [ ] Poster files backup configured
  - [ ] Configuration backups automated

- [ ] **Monitoring**
  - [ ] Health check endpoints working
  - [ ] Log aggregation configured
  - [ ] Resource monitoring setup
  - [ ] Alerts configured

- [ ] **Testing**
  - [ ] All services start successfully
  - [ ] Health checks pass
  - [ ] Poster generation works end-to-end
  - [ ] API endpoints respond correctly

---

## Advanced Topics

### Custom Dockerfile Modifications

To add custom dependencies:

```dockerfile
# In Dockerfile, after pip install
RUN pip install --no-cache-dir your-package==1.0.0
```

Then rebuild:
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Multi-Stage Builds

The [`Dockerfile`](../Dockerfile) uses multi-stage builds:
- **Stage 1 (builder)**: Compiles dependencies
- **Stage 2 (runtime)**: Final production image

This reduces image size by ~40%.

### Networking

Services communicate via Docker network `maptoposter-net`:

```bash
# Inspect network
docker network inspect maptoposter-web_maptoposter-net

# Test connectivity
docker-compose exec web ping postgres
docker-compose exec web ping redis
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect postgres_data

# Backup volume
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

### SSL/TLS with Let's Encrypt

```bash
# Install certbot
docker-compose run --rm certbot certonly --webroot \
  -w /var/www/certbot \
  -d yourdomain.com \
  -d www.yourdomain.com

# Update nginx.conf with certificate paths
# Restart nginx
docker-compose restart nginx

# Auto-renewal cron job
0 0 * * * docker-compose run --rm certbot renew && docker-compose restart nginx
```

### Performance Tuning

**Web workers**:
```yaml
# docker-compose.yml
command: gunicorn --bind 0.0.0.0:5000 --workers 8 --timeout 300 run:app
```

**Celery concurrency**:
```yaml
command: celery -A celery_worker.celery worker --concurrency=4
```

**PostgreSQL tuning**:
```yaml
environment:
  POSTGRES_SHARED_BUFFERS: 256MB
  POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
```

**Redis memory**:
```yaml
command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
```

---

## See Also

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [Web Architecture](WEB_ARCHITECTURE.md) - Technical architecture details
- [Docker README](../DOCKER_README.md) - Quick reference guide
- [Main README](../README.md) - Project overview