#!/bin/bash

# City Map Poster Generator - Stop Development Services

echo "Stopping development services..."

# PID file locations
FLASK_PID="./pids/flask.pid"
CELERY_PID="./pids/celery.pid"

stopped=0

# Stop Flask
if [ -f "$FLASK_PID" ]; then
    FLASK_PID_NUM=$(cat "$FLASK_PID")
    if kill -0 "$FLASK_PID_NUM" 2>/dev/null; then
        kill "$FLASK_PID_NUM"
        echo "  ✓ Flask stopped (PID: $FLASK_PID_NUM)"
        stopped=1
    fi
    rm -f "$FLASK_PID"
fi

# Stop Celery
if [ -f "$CELERY_PID" ]; then
    CELERY_PID_NUM=$(cat "$CELERY_PID")
    if kill -0 "$CELERY_PID_NUM" 2>/dev/null; then
        kill "$CELERY_PID_NUM"
        echo "  ✓ Celery stopped (PID: $CELERY_PID_NUM)"
        stopped=1
    fi
    rm -f "$CELERY_PID"
fi

if [ $stopped -eq 0 ]; then
    echo "  No services were running"
fi

echo ""
echo "Note: Redis is left running. To stop Redis:"
echo "  • Docker: docker stop maptoposter-redis"
echo "  • Local: redis-cli shutdown"