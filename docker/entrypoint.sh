#!/bin/bash
# Docker entrypoint script for City Map Poster Generator
# This script handles service initialization and startup

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}City Map Poster Generator - Entrypoint${NC}"
echo -e "${GREEN}========================================${NC}"

# ============================================================================
# Wait for Service Functions
# ============================================================================

# Wait for PostgreSQL to be ready
wait_for_postgres() {
    if [[ $DATABASE_URL == postgresql://* ]]; then
        echo -e "${YELLOW}Waiting for PostgreSQL...${NC}"
        
        # Extract connection details from DATABASE_URL
        # Format: postgresql://user:pass@host:port/db
        DB_HOST=$(echo $DATABASE_URL | sed -E 's/postgresql:\/\/[^@]+@([^:]+).*/\1/')
        DB_PORT=$(echo $DATABASE_URL | sed -E 's/postgresql:\/\/[^:]+:[^@]+@[^:]+:([0-9]+).*/\1/')
        
        # Default to standard port if not specified
        DB_PORT=${DB_PORT:-5432}
        
        # Wait for PostgreSQL to accept connections
        until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "maptoposter" -p "$DB_PORT" -c '\q' 2>/dev/null; do
            echo -e "${YELLOW}PostgreSQL is unavailable - sleeping${NC}"
            sleep 2
        done
        
        echo -e "${GREEN}PostgreSQL is up and running!${NC}"
    else
        echo -e "${YELLOW}Using SQLite - skipping PostgreSQL check${NC}"
    fi
}

# Wait for Redis to be ready
wait_for_redis() {
    echo -e "${YELLOW}Waiting for Redis...${NC}"
    
    # Extract host and port from REDIS_URL
    # Format: redis://host:port/db
    REDIS_HOST=$(echo $REDIS_URL | sed -E 's/redis:\/\/([^:]+).*/\1/')
    REDIS_PORT=$(echo $REDIS_URL | sed -E 's/redis:\/\/[^:]+:([0-9]+).*/\1/')
    
    # Default to standard port if not specified
    REDIS_PORT=${REDIS_PORT:-6379}
    
    # Wait for Redis to respond to PING
    until redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null | grep -q PONG; do
        echo -e "${YELLOW}Redis is unavailable - sleeping${NC}"
        sleep 2
    done
    
    echo -e "${GREEN}Redis is up and running!${NC}"
}

# ============================================================================
# Database Initialization
# ============================================================================

init_database() {
    echo -e "${YELLOW}Initializing database...${NC}"
    
    # Create instance directory if it doesn't exist
    mkdir -p /app/instance
    
    # Run database migrations using Flask-SQLAlchemy
    python << END
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    # Create all tables
    db.create_all()
    print("Database tables created successfully!")
END
    
    echo -e "${GREEN}Database initialized!${NC}"
}

# ============================================================================
# Storage Directory Setup
# ============================================================================

setup_storage() {
    echo -e "${YELLOW}Setting up storage directories...${NC}"
    
    # Create storage directories if they don't exist
    mkdir -p "${POSTER_STORAGE_PATH:-/app/posters}"
    mkdir -p "${THUMBNAIL_STORAGE_PATH:-/app/thumbnails}"
    mkdir -p "${TEMP_STORAGE_PATH:-/app/temp}"
    
    # Set permissions (already running as appuser, so just verify)
    echo -e "${GREEN}Storage directories ready!${NC}"
}

# ============================================================================
# Main Execution
# ============================================================================

# Wait for dependent services
wait_for_redis
wait_for_postgres

# Initialize database (only if needed)
if [[ "${INIT_DB:-true}" == "true" ]]; then
    init_database
fi

# Setup storage directories
setup_storage

# Execute the provided command
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting application...${NC}"
echo -e "${GREEN}Command: $@${NC}"
echo -e "${GREEN}========================================${NC}"

# Execute the command passed to the entrypoint
exec "$@"