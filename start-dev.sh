#!/bin/bash

# City Map Poster Generator - Development Startup Script
# This script starts all required services for local development

set -e

echo "=================================================="
echo "City Map Poster Generator - Starting Dev Services"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Redis is running
check_redis() {
    if command_exists redis-cli; then
        redis-cli ping >/dev/null 2>&1
        return $?
    fi
    return 1
}

# Function to check if Docker is running
check_docker() {
    if command_exists docker; then
        docker ps >/dev/null 2>&1
        return $?
    fi
    return 1
}

# Function to start Redis in Docker
start_redis_docker() {
    echo -e "${YELLOW}Starting Redis in Docker...${NC}"
    
    # Check if container already exists
    if docker ps -a --format '{{.Names}}' | grep -q '^maptoposter-redis$'; then
        echo "  Container 'maptoposter-redis' already exists"
        
        # Check if it's running
        if docker ps --format '{{.Names}}' | grep -q '^maptoposter-redis$'; then
            echo -e "  ${GREEN}✓ Redis is already running${NC}"
            return 0
        else
            echo "  Starting existing container..."
            docker start maptoposter-redis
            sleep 2
            echo -e "  ${GREEN}✓ Redis started${NC}"
            return 0
        fi
    else
        # Create and start new container
        docker run -d --name maptoposter-redis -p 6379:6379 redis:alpine
        sleep 2
        echo -e "  ${GREEN}✓ Redis started in Docker${NC}"
        return 0
    fi
}

# Function to start Redis locally
start_redis_local() {
    echo -e "${YELLOW}Attempting to start Redis locally...${NC}"
    
    if command_exists redis-server; then
        # Start Redis in background
        redis-server --daemonize yes --port 6379
        sleep 2
        
        if check_redis; then
            echo -e "  ${GREEN}✓ Redis started locally${NC}"
            return 0
        else
            echo -e "  ${RED}✗ Failed to start Redis locally${NC}"
            return 1
        fi
    else
        echo -e "  ${RED}✗ redis-server not found${NC}"
        return 1
    fi
}

# PID file locations
FLASK_PID="./pids/flask.pid"
CELERY_PID="./pids/celery.pid"

# Create pids directory if it doesn't exist
mkdir -p pids

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping services..."
    
    if [ -f "$FLASK_PID" ]; then
        FLASK_PID_NUM=$(cat "$FLASK_PID")
        if kill -0 "$FLASK_PID_NUM" 2>/dev/null; then
            kill "$FLASK_PID_NUM"
            echo "  ✓ Flask stopped"
        fi
        rm -f "$FLASK_PID"
    fi
    
    if [ -f "$CELERY_PID" ]; then
        CELERY_PID_NUM=$(cat "$CELERY_PID")
        if kill -0 "$CELERY_PID_NUM" 2>/dev/null; then
            kill "$CELERY_PID_NUM"
            echo "  ✓ Celery stopped"
        fi
        rm -f "$CELERY_PID"
    fi
}

# Trap Ctrl+C to cleanup
trap cleanup EXIT INT TERM

# Step 1: Check/Start Redis
echo "Step 1: Redis Check"
echo "-------------------"

if check_redis; then
    echo -e "${GREEN}✓ Redis is already running${NC}"
else
    echo "Redis is not running. Attempting to start..."
    
    # Try Docker first, then local Redis
    if check_docker; then
        if start_redis_docker; then
            :  # Success
        else
            echo -e "${RED}✗ Failed to start Redis in Docker${NC}"
            exit 1
        fi
    else
        echo "Docker not available, trying local Redis..."
        if ! start_redis_local; then
            echo ""
            echo -e "${RED}ERROR: Could not start Redis${NC}"
            echo ""
            echo "Please install Redis using one of these methods:"
            echo "  1. Docker: brew install docker"
            echo "  2. Redis locally: brew install redis"
            echo ""
            exit 1
        fi
    fi
fi

echo ""

# Step 2: Check Virtual Environment
echo "Step 2: Virtual Environment"
echo "---------------------------"

if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment found${NC}"
    source venv/bin/activate
    echo "  Activated: venv"
else
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo ""
    echo "Please create a virtual environment first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements-web.txt"
    echo ""
    exit 1
fi

echo ""

# Step 3: Start Flask Server
echo "Step 3: Starting Flask Server"
echo "------------------------------"

export FLASK_ENV=development
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000

python run.py > logs/flask.log 2>&1 &
FLASK_PID_NUM=$!
echo $FLASK_PID_NUM > "$FLASK_PID"

sleep 3

if kill -0 "$FLASK_PID_NUM" 2>/dev/null; then
    echo -e "${GREEN}✓ Flask server started (PID: $FLASK_PID_NUM)${NC}"
    echo "  URL: http://localhost:5000"
else
    echo -e "${RED}✗ Flask server failed to start${NC}"
    echo "  Check logs/flask.log for errors"
    exit 1
fi

echo ""

# Step 4: Start Celery Worker
echo "Step 4: Starting Celery Worker"
echo "-------------------------------"

python celery_worker.py > logs/celery.log 2>&1 &
CELERY_PID_NUM=$!
echo $CELERY_PID_NUM > "$CELERY_PID"

sleep 3

if kill -0 "$CELERY_PID_NUM" 2>/dev/null; then
    echo -e "${GREEN}✓ Celery worker started (PID: $CELERY_PID_NUM)${NC}"
else
    echo -e "${RED}✗ Celery worker failed to start${NC}"
    echo "  Check logs/celery.log for errors"
    exit 1
fi

echo ""

# Summary
echo "=================================================="
echo "All Services Running!"
echo "=================================================="
echo ""
echo "Service Status:"
echo "  • Redis:   Running"
echo "  • Flask:   http://localhost:5000 (PID: $FLASK_PID_NUM)"
echo "  • Celery:  Running (PID: $CELERY_PID_NUM)"
echo ""
echo "Logs:"
echo "  • Flask:  logs/flask.log"
echo "  • Celery: logs/celery.log"
echo ""
echo "To stop all services:"
echo "  • Press Ctrl+C (if running in foreground)"
echo "  • Or run: ./stop-dev.sh"
echo "  • Or manually:"
echo "      kill $FLASK_PID_NUM   # Stop Flask"
echo "      kill $CELERY_PID_NUM  # Stop Celery"
echo ""
echo "=================================================="
echo ""

# Keep script running (allows Ctrl+C to cleanup)
echo "Press Ctrl+C to stop all services..."
wait