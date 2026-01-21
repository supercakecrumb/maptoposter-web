# Setup Guide - City Map Poster Generator

This guide covers the recent fixes and improvements to the web application.

## 🔧 Recent Fixes

### 1. Development Startup Script
**Problem**: No easy way to start all required services for local development.

**Solution**: Created `start-dev.sh` that automatically:
- Checks if Redis is running (Docker or local)
- Starts Redis if needed
- Activates virtual environment
- Starts Flask server
- Starts Celery worker
- Shows service status and logs

### 2. Synchronous Task Execution for Development
**Problem**: Jobs were stuck in "Pending" state because Celery worker wasn't running or couldn't access SQLite database.

**Solution**: Added `CELERY_TASK_ALWAYS_EAGER = True` to development config in [`app/config.py`](app/config.py). This makes Celery execute tasks synchronously (no separate worker needed), perfect for local development.

### 3. Theme Preview Images
**Problem**: Theme gallery showed "Preview" placeholder text instead of actual preview images.

**Solution**: 
- Created [`scripts/generate_theme_previews.py`](scripts/generate_theme_previews.py) to generate preview images for all themes
- Updated [`app/services/theme_service.py`](app/services/theme_service.py) to point to correct preview URLs
- Updated [`app/templates/themes.html`](app/templates/themes.html) to display actual images
- Preview images saved to `app/static/images/themes/`

### 4. Session Tracking
**Status**: Already working correctly! No fixes needed.
- Jobs store `session_id` when created
- Posters inherit `session_id` from jobs
- Gallery filters posters by current session
- No user accounts needed - just browser session-based tracking

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** with virtual environment
2. **Redis** (via Docker or locally installed)

### Installation

```bash
# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements-web.txt
```

### Running the Application

#### Option 1: Using the Startup Script (Recommended)

```bash
./start-dev.sh
```

This will:
- Start Redis (if not running)
- Start Flask server on http://localhost:5000
- Start Celery worker
- Show service status

To stop all services:
```bash
./stop-dev.sh
# or press Ctrl+C if start-dev.sh is running in foreground
```

#### Option 2: Manual Startup

```bash
# Terminal 1: Start Redis (if using Docker)
docker run -d --name maptoposter-redis -p 6379:6379 redis:alpine

# Terminal 2: Start Flask
source venv/bin/activate
python run.py

# Terminal 3: Start Celery worker (optional in dev mode)
source venv/bin/activate
python celery_worker.py
```

**Note**: In development mode, Celery worker is optional because tasks run synchronously.

### Generating Theme Previews

Generate preview images for all themes:

```bash
source venv/bin/activate
python scripts/generate_theme_previews.py
```

This will:
- Download map data for Paris (used as preview city)
- Generate preview images for all 17 themes
- Save previews to `app/static/images/themes/`
- Takes ~5-10 minutes to complete

## 📁 Project Structure

```
maptoposter-web/
├── start-dev.sh              # Development startup script (NEW)
├── stop-dev.sh               # Stop all services (NEW)
├── scripts/
│   └── generate_theme_previews.py  # Theme preview generator (NEW)
├── app/
│   ├── config.py             # Added CELERY_TASK_ALWAYS_EAGER for dev
│   ├── services/
│   │   └── theme_service.py  # Updated preview URLs
│   ├── templates/
│   │   ├── themes.html       # Updated to show preview images
│   │   └── gallery.html      # Session-based poster display
│   └── static/
│       └── images/
│           └── themes/       # Theme preview images (NEW)
├── logs/                     # Application logs (created by start-dev.sh)
└── pids/                     # Process IDs (created by start-dev.sh)
```

## 🔍 Configuration Modes

### Development Mode (Default)
- **Celery**: Tasks run synchronously (CELERY_TASK_ALWAYS_EAGER = True)
- **Debug**: Enabled
- **Auto-reload**: Enabled
- **Benefits**: No need for separate Celery worker, easier debugging

### Production Mode
- **Celery**: Tasks run asynchronously with worker
- **Debug**: Disabled
- **Worker**: Required for background processing
- **Deploy**: Use Docker Compose (see DOCKER_README.md)

## 🧪 Testing the Fixes

### Test 1: Poster Generation (No Longer Stuck in Pending)

1. Start the application: `./start-dev.sh`
2. Navigate to http://localhost:5000
3. Create a poster (e.g., "Paris, France")
4. **Expected**: Job completes successfully (not stuck in "Pending")
5. Check gallery - poster should appear

### Test 2: Session Tracking

1. Create a poster
2. Navigate to Gallery page
3. **Expected**: See the poster you just created
4. Open in incognito/private window
5. **Expected**: Gallery is empty (different session)

### Test 3: Theme Previews

1. Generate previews: `python scripts/generate_theme_previews.py`
2. Navigate to Themes page: http://localhost:5000/themes
3. **Expected**: See actual preview images for all 17 themes (not "Preview" text)

## 🐛 Troubleshooting

### Redis Not Starting

**Docker method:**
```bash
# Check if Docker is running
docker ps

# Remove existing container if needed
docker stop maptoposter-redis
docker rm maptoposter-redis

# Start fresh
docker run -d --name maptoposter-redis -p 6379:6379 redis:alpine
```

**Local Redis method:**
```bash
# Install Redis
brew install redis  # macOS
sudo apt install redis-server  # Ubuntu

# Start Redis
redis-server --daemonize yes
```

### Jobs Still Stuck in Pending

**Check configuration:**
1. Verify `CELERY_TASK_ALWAYS_EAGER = True` in [`app/config.py`](app/config.py) DevelopmentConfig
2. Restart Flask: `./stop-dev.sh && ./start-dev.sh`
3. Check logs: `tail -f logs/flask.log`

### Theme Previews Not Showing

**Generate previews:**
```bash
source venv/bin/activate
python scripts/generate_theme_previews.py
```

**Check files exist:**
```bash
ls -la app/static/images/themes/
# Should show: *_preview.png files
```

### Gallery Empty

**Check session:**
1. Create a poster first
2. Don't open gallery in incognito mode
3. Check browser cookies are enabled
4. Look in database:
```bash
sqlite3 posters.db "SELECT id, city, session_id FROM posters;"
```

## 📊 Logs and Monitoring

### Log Files
- **Flask**: `logs/flask.log`
- **Celery**: `logs/celery.log`

### View Logs in Real-Time
```bash
# Flask logs
tail -f logs/flask.log

# Celery logs
tail -f logs/celery.log

# Both
tail -f logs/*.log
```

### Check Service Status
```bash
# Check if Flask is running
ps aux | grep "python run.py"

# Check if Celery is running
ps aux | grep "celery_worker"

# Check Redis
redis-cli ping
# Should return: PONG
```

## 🔧 Environment Variables

Key environment variables (optional, defaults provided):

```bash
# Flask
FLASK_ENV=development          # development/production
FLASK_HOST=0.0.0.0            # Listen address
FLASK_PORT=5000               # Port number

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Database
DATABASE_URL=sqlite:///posters.db
```

## 📚 Additional Resources

- **API Documentation**: See `docs/API_REFERENCE.md`
- **Docker Deployment**: See `DOCKER_README.md`
- **Technical Overview**: See `docs/TECHNICAL_OVERVIEW.md`
- **Theme System**: See `docs/THEME_SYSTEM.md`

## 🎉 What's Working Now

✅ **Single command startup** - `./start-dev.sh` starts everything  
✅ **No pending jobs** - Tasks execute immediately in dev mode  
✅ **Theme previews** - Gallery shows actual preview images  
✅ **Session tracking** - Gallery shows your posters only  
✅ **Easy debugging** - Synchronous execution, detailed logs  
✅ **Clean shutdown** - `./stop-dev.sh` or Ctrl+C stops all services

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review log files in `logs/`
3. Ensure Redis is running: `redis-cli ping`
4. Verify virtual environment is activated
5. Try a fresh restart: `./stop-dev.sh && ./start-dev.sh`

---

**Last Updated**: January 19, 2026  
**Version**: 2.0 (Development Mode Fixes)