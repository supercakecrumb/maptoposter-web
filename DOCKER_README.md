# Docker Deployment Guide

Complete guide for deploying the City Map Poster Generator using Docker.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Deployment Modes](#deployment-modes)
- [Management Commands](#management-commands)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Monitoring](#monitoring)

## 🔧 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- 10GB disk space for images and data

## 🚀 Quick Start

### Development Mode

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env with your settings
nano .env

# 3. Start services with development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 4. View logs
docker-compose logs -f web

# 5. Access application
open http://localhost:5000
```

### Production Mode (Basic)

```bash
# 1. Set production environment variables
cp .env.example .env
# Edit .env and set:
#   - FLASK_ENV=production
#   - SECRET_KEY=<generate-secure-random-key>
#   - POSTGRES_PASSWORD=<strong-password>

# 2. Start services
docker-compose up -d

# 3. Check health
docker-compose ps
curl http://localhost:5000/api/v1/health
```

### Production Mode (with Nginx)

```bash
# 1. Configure SSL certificates (optional but recommended)
mkdir -p docker/ssl
# Copy your SSL certificates to docker/ssl/

# 2. Start all services including Nginx
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 3. Access via Nginx
curl http://localhost/api/v1/health
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# PostgreSQL
POSTGRES_PASSWORD=your-postgres-password

# Database URL
DATABASE_URL=postgresql://maptoposter:your-postgres-password@postgres:5432/maptoposter

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

# Generate POSTGRES_PASSWORD
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

## 🏗️ Deployment Modes

### 1. Development Mode

**Features:**
- Hot code reloading
- SQLite database (simpler)
- Debug mode enabled
- Source code mounted as volumes
- Exposed Redis port for debugging

**Usage:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 2. Production Mode (Basic)

**Features:**
- PostgreSQL database
- Gunicorn WSGI server
- Resource limits
- Health checks
- Auto-restart

**Usage:**
```bash
docker-compose up -d
```

### 3. Production Mode (with Nginx)

**Features:**
- All features from basic production
- Nginx reverse proxy
- SSL/TLS support
- Static file serving
- Rate limiting
- Gzip compression

**Usage:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📦 Management Commands

### Build and Deploy

```bash
# Build images
docker-compose build

# Build without cache
docker-compose build --no-cache

# Start services
docker-compose up -d

# Start specific service
docker-compose up -d web

# Scale celery workers
docker-compose up -d --scale celery=3
```

### Monitoring

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f web
docker-compose logs -f celery

# Check service status
docker-compose ps

# Check resource usage
docker stats
```

### Database Management

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U maptoposter -d maptoposter

# Backup database
docker-compose exec postgres pg_dump -U maptoposter maptoposter > backup.sql

# Restore database
docker-compose exec -T postgres psql -U maptoposter maptoposter < backup.sql

# Initialize database tables
docker-compose exec web python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Redis Management

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHDB

# Monitor Redis
docker-compose exec redis redis-cli MONITOR
```

### Celery Management

```bash
# Check celery worker status
docker-compose exec celery celery -A celery_worker.celery inspect active

# Purge all tasks
docker-compose exec celery celery -A celery_worker.celery purge

# Restart celery worker
docker-compose restart celery
```

### Cleanup

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

## 🌐 Production Deployment

### SSL/TLS Configuration

#### Option 1: Using Let's Encrypt (Recommended)

```bash
# 1. Install certbot
docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm \
  certbot certonly --webroot -w /var/www/certbot \
  -d yourdomain.com -d www.yourdomain.com

# 2. Update nginx.conf with certificate paths
# Edit docker/nginx.conf:
#   ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
#   ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

# 3. Restart nginx
docker-compose restart nginx
```

#### Option 2: Self-Signed Certificate (Development/Testing)

```bash
# Generate self-signed certificate
mkdir -p docker/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/ssl/key.pem \
  -out docker/ssl/cert.pem \
  -subj "/CN=localhost"
```

### Resource Limits

Edit `docker-compose.yml` to adjust resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'      # Maximum CPUs
      memory: 2G     # Maximum memory
    reservations:
      cpus: '1'      # Minimum CPUs
      memory: 1G     # Minimum memory
```

### Monitoring and Logging

#### View Application Logs

```bash
# Real-time logs
docker-compose logs -f web celery

# Last 100 lines
docker-compose logs --tail=100 web

# Save logs to file
docker-compose logs web > web.log
```

#### Health Checks

```bash
# Check all services
docker-compose ps

# Check web health endpoint
curl http://localhost:5000/api/v1/health

# Check through nginx
curl http://localhost/api/v1/health
```

### Backup Strategy

#### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
docker-compose exec -T postgres pg_dump -U maptoposter maptoposter > "$BACKUP_DIR/database.sql"

# Backup volumes
docker run --rm -v maptoposter-web_poster_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/posters.tar.gz -C /data .

echo "Backup completed: $BACKUP_DIR"
```

## 🔍 Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "5001:5000"
```

#### Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Wait for PostgreSQL to be ready
docker-compose exec web python -c "
from sqlalchemy import create_engine
from time import sleep
import os
engine = create_engine(os.environ['DATABASE_URL'])
for i in range(30):
    try:
        engine.connect()
        print('Connected!')
        break
    except:
        print('Waiting...')
        sleep(1)
"
```

#### Celery Worker Not Processing Tasks

```bash
# Check celery worker status
docker-compose logs celery

# Check Redis connection
docker-compose exec celery python -c "
from redis import Redis
import os
r = Redis.from_url(os.environ['REDIS_URL'])
print(r.ping())
"

# Restart celery
docker-compose restart celery
```

#### Permission Denied Errors

```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix volume permissions
docker-compose exec web chown -R appuser:appuser /app/posters /app/thumbnails /app/temp
```

#### Out of Memory

```bash
# Check memory usage
docker stats

# Increase memory limits in docker-compose.yml
# Or reduce number of workers

# For development, reduce Celery concurrency
command: celery -A celery_worker.celery worker --concurrency=1
```

### Debug Mode

Enable debug logging:

```bash
# Set in .env
FLASK_ENV=development
FLASK_DEBUG=1

# Restart services
docker-compose restart web celery

# View detailed logs
docker-compose logs -f web
```

### Access Container Shell

```bash
# Access web container
docker-compose exec web /bin/bash

# Access as root (for debugging)
docker-compose exec -u root web /bin/bash

# Run Python shell
docker-compose exec web python
```

## 📊 Monitoring

### Health Endpoints

- **Web Application**: `http://localhost:5000/api/v1/health`
- **Redis**: `docker-compose exec redis redis-cli ping`
- **PostgreSQL**: `docker-compose exec postgres pg_isready`

### Prometheus Metrics (Future Enhancement)

Add Prometheus monitoring by installing `prometheus-flask-exporter`:

```python
# In app/__init__.py
from prometheus_flask_exporter import PrometheusMetrics

def create_app():
    app = Flask(__name__)
    metrics = PrometheusMetrics(app)
    # ...
```

### Log Aggregation

Use Docker logging drivers:

```yaml
# In docker-compose.yml
services:
  web:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔐 Security Best Practices

1. **Never commit `.env` file to version control**
2. **Use strong passwords** for database and SECRET_KEY
3. **Enable SSL/TLS** in production
4. **Run containers as non-root user** (already configured)
5. **Keep Docker images updated**: `docker-compose pull && docker-compose up -d`
6. **Use secrets management** for production (e.g., Docker Swarm secrets, Kubernetes secrets)
7. **Implement rate limiting** (configured in nginx.conf)
8. **Regular backups** of database and generated posters

## 📝 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)

## 🤝 Support

For issues and questions:
1. Check the [troubleshooting section](#troubleshooting)
2. Review application logs: `docker-compose logs -f`
3. Consult the main [README.md](README.md)
4. Check [WEB_README.md](WEB_README.md) for API documentation