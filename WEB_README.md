# City Map Poster Generator - Web Application

Flask web application for generating beautiful city map posters with background job processing.

## Features

- **REST API** for poster generation
- **Background Processing** with Celery + Redis
- **Session-based tracking** (no login required)
- **17 beautiful themes** to choose from
- **Responsive UI** built with Alpine.js and Tailwind CSS
- **Real-time progress tracking** for poster generation
- **Gallery** to view and download your generated posters

## Quick Start

### Prerequisites

- Python 3.8+
- Redis server (for Celery and caching)

### Installation

1. **Install dependencies:**

```bash
# Install base dependencies
pip install -r requirements.txt

# Install web application dependencies
pip install -r requirements-web.txt
```

2. **Configure environment:**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings (optional for development)
```

3. **Start Redis** (in a separate terminal):

```bash
redis-server
```

### Running the Application

You need to run **three processes** simultaneously:

#### Terminal 1: Flask Web Server

```bash
python run.py
```

The web application will be available at: http://localhost:5000

#### Terminal 2: Celery Worker

```bash
python celery_worker.py
```

This handles background poster generation tasks.

#### Terminal 3: Redis (if not running as service)

```bash
redis-server
```

## Usage

1. Open http://localhost:5000 in your browser
2. Enter a city name and country
3. Select a theme from the gallery
4. Adjust the map radius (optional)
5. Click "Create Poster"
6. Watch the progress in real-time
7. Download your generated poster!

## Project Structure

```
app/
├── __init__.py              # Flask app factory
├── config.py                # Configuration
├── extensions.py            # Flask extensions
├── models.py                # Database models
├── api/                     # REST API endpoints
│   ├── themes.py
│   ├── geocoding.py
│   ├── posters.py
│   ├── jobs.py
│   └── health.py
├── services/                # Business logic
│   ├── theme_service.py
│   ├── geocoding_service.py
│   └── poster_service.py
├── tasks/                   # Celery background tasks
│   └── poster_tasks.py
├── utils/                   # Utilities
│   └── cli_wrapper.py       # Wraps existing CLI code
├── web/                     # Web routes
│   └── __init__.py
├── templates/               # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   ├── create.html
│   ├── progress.html
│   ├── result.html
│   └── gallery.html
└── static/                  # Static assets
    ├── css/style.css
    └── js/app.js
```

## API Endpoints

### Themes

- `GET /api/v1/themes` - List all themes
- `GET /api/v1/themes/{id}` - Get theme details

### Geocoding

- `GET /api/v1/geocode?city={city}&country={country}` - Geocode location

### Posters

- `POST /api/v1/posters` - Create poster generation job
- `GET /api/v1/posters` - List user's posters
- `GET /api/v1/posters/{id}` - Get poster details
- `GET /api/v1/posters/{id}/download` - Download poster

### Jobs

- `GET /api/v1/jobs/{id}` - Get job status
- `POST /api/v1/jobs/{id}/cancel` - Cancel job

### Health

- `GET /api/v1/health` - Health check

## Configuration

Environment variables (see `.env.example`):

- `FLASK_ENV` - Environment (development/production)
- `SECRET_KEY` - Flask secret key
- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis connection string
- `CELERY_BROKER_URL` - Celery broker URL
- `CELERY_RESULT_BACKEND` - Celery result backend URL

## Development

### Database

The application uses SQLite by default for development. The database file `posters.db` will be created automatically.

For production, use PostgreSQL:

```
DATABASE_URL=postgresql://user:password@localhost:5432/mapposters
```

### Testing

```bash
# Run Flask development server with auto-reload
FLASK_ENV=development python run.py

# Run Celery worker with auto-reload
celery -A celery_worker.celery worker --loglevel=info --reload
```

### Debugging

Check logs:
- Flask logs appear in the terminal running `run.py`
- Celery logs appear in the terminal running `celery_worker.py`
- Redis logs can be viewed with `redis-cli monitor`

## Architecture Highlights

- **Flask app factory pattern** for flexible configuration
- **Service layer** separates business logic from API routes
- **CLI wrapper** reuses existing poster generation code without modification
- **Celery tasks** handle long-running poster generation
- **Redis caching** for geocoding results and theme data
- **Session-based tracking** for anonymous users
- **Alpine.js** for reactive frontend components

## Troubleshooting

### Redis connection error

Make sure Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### Celery not processing tasks

1. Check if Celery worker is running
2. Check Redis connection
3. Look for errors in Celery worker terminal

### Database errors

Delete and recreate the database:
```bash
rm posters.db
python run.py  # Will create new database
```

## Production Deployment

For production deployment, see [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md).

Key considerations:
- Use Gunicorn instead of Flask development server
- Use PostgreSQL instead of SQLite
- Set up proper Redis persistence
- Configure Nginx as reverse proxy
- Use environment variables for secrets
- Set up monitoring and logging

## Next Steps

See [`docs/WEB_ARCHITECTURE.md`](docs/WEB_ARCHITECTURE.md) for:
- Phase 2 features (preview generation, interactive map)
- Phase 3 features (custom themes, user accounts)
- Performance optimization strategies
- Security best practices

## Support

For issues or questions, refer to:
- [`docs/TECHNICAL_OVERVIEW.md`](docs/TECHNICAL_OVERVIEW.md) - CLI system architecture
- [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) - Detailed API documentation
- [`docs/WEB_ARCHITECTURE.md`](docs/WEB_ARCHITECTURE.md) - Web app architecture

## License

See [LICENSE](LICENSE) file for details.