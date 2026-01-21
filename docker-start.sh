#!/bin/bash
# Quick start script for Docker deployment
# This script helps initialize and start the Docker environment

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}City Map Poster Generator${NC}"
echo -e "${BLUE}Docker Quick Start${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    
    if [ -f .env.docker ]; then
        cp .env.docker .env
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env and update these values:${NC}"
        echo "  - SECRET_KEY (generate with: python -c 'import secrets; print(secrets.token_hex(32))')"
        echo "  - POSTGRES_PASSWORD (generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))')"
        echo "  - Update DATABASE_URL with your postgres password"
        echo ""
        read -p "Press Enter after updating .env file..."
    else
        echo -e "${RED}Error: .env.docker template not found${NC}"
        exit 1
    fi
fi

# Display deployment mode menu
echo -e "${BLUE}Select deployment mode:${NC}"
echo "1) Development (SQLite, hot reload, debug mode)"
echo "2) Production - Basic (PostgreSQL, gunicorn)"
echo "3) Production - with Nginx (PostgreSQL, gunicorn, nginx)"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo -e "${GREEN}Starting in Development mode...${NC}"
        COMPOSE_CMD="docker-compose -f docker-compose.yml -f docker-compose.dev.yml"
        ;;
    2)
        echo -e "${GREEN}Starting in Production mode (basic)...${NC}"
        COMPOSE_CMD="docker-compose"
        ;;
    3)
        echo -e "${GREEN}Starting in Production mode (with Nginx)...${NC}"
        COMPOSE_CMD="docker-compose -f docker-compose.yml -f docker-compose.prod.yml"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Build images
echo ""
echo -e "${YELLOW}Building Docker images...${NC}"
$COMPOSE_CMD build

# Start services
echo ""
echo -e "${YELLOW}Starting services...${NC}"
$COMPOSE_CMD up -d

# Wait for services to be ready
echo ""
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Check service health
echo ""
echo -e "${YELLOW}Checking service health...${NC}"
$COMPOSE_CMD ps

# Test health endpoint
echo ""
if curl -f http://localhost:5000/api/v1/health &> /dev/null; then
    echo -e "${GREEN}✓ Application is running!${NC}"
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}Deployment successful!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "Access the application at:"
    
    if [ "$choice" == "3" ]; then
        echo -e "  ${GREEN}http://localhost${NC} (via Nginx)"
    else
        echo -e "  ${GREEN}http://localhost:5000${NC}"
    fi
    
    echo ""
    echo "Useful commands:"
    echo "  - View logs: $COMPOSE_CMD logs -f"
    echo "  - Stop services: $COMPOSE_CMD down"
    echo "  - Restart: $COMPOSE_CMD restart"
    echo ""
    echo "See DOCKER_README.md for more information"
else
    echo -e "${RED}✗ Application health check failed${NC}"
    echo ""
    echo "View logs with: $COMPOSE_CMD logs -f"
    exit 1
fi