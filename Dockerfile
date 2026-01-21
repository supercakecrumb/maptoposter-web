# Multi-stage Dockerfile for City Map Poster Generator
# Uses Python 3.11 for SQLAlchemy compatibility

# ============================================================================
# Stage 1: Builder - Install dependencies and build wheels
# ============================================================================
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /build

# Install build dependencies for geospatial libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-web.txt ./

# Create wheels for all dependencies to speed up final image build
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels \
    -r requirements.txt \
    -r requirements-web.txt

# ============================================================================
# Stage 2: Runtime - Final production image
# ============================================================================
FROM python:3.11-slim

# Set metadata
LABEL maintainer="City Map Poster Generator"
LABEL description="Flask web application for generating artistic city map posters"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLASK_APP=run.py

# Install runtime dependencies for geospatial libraries and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal32 \
    libgeos-c1v5 \
    libproj25 \
    libspatialindex6 \
    # Font dependencies for Roboto fonts
    fontconfig \
    fonts-liberation \
    # Additional utilities
    curl \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for running the application
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /build/wheels /tmp/wheels

# Install Python dependencies from wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /tmp/wheels/*.whl && \
    # Install gunicorn for production WSGI server
    pip install --no-cache-dir gunicorn==21.2.0 && \
    # Cleanup wheels
    rm -rf /tmp/wheels

# Copy application code
COPY --chown=appuser:appuser . .

# Copy and set permissions for entrypoint script
COPY --chown=appuser:appuser docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/posters /app/thumbnails /app/temp /app/instance && \
    chown -R appuser:appuser /app/posters /app/thumbnails /app/temp /app/instance

# Switch to non-root user
USER appuser

# Expose Flask application port
EXPOSE 5000

# Health check - ping the Flask health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

# Default command - run with gunicorn
# Override this in docker-compose for different services (web vs celery)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-", "run:app"]