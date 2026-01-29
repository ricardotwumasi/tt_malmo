#!/bin/bash
# =============================================================================
# Start Malmo in Docker
# =============================================================================
#
# This script starts Minecraft with Malmo mod in a Linux Docker container,
# bypassing macOS compatibility issues.
#
# Prerequisites:
#   - Docker Desktop installed and running
#   - Rosetta 2 enabled for Docker (for Apple Silicon)
#
# Usage:
#   ./start_docker_malmo.sh          # Start Malmo only
#   ./start_docker_malmo.sh --full   # Start full stack (Malmo + MCP Server + DB)
#   ./start_docker_malmo.sh --stop   # Stop containers
#   ./start_docker_malmo.sh --logs   # View Malmo logs
#
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_banner() {
    echo ""
    echo "=============================================="
    echo "  Malmo Docker Setup"
    echo "=============================================="
    echo ""
}

check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running.${NC}"
        echo "Please start Docker Desktop and try again."
        exit 1
    fi
    echo -e "${GREEN}✓ Docker is running${NC}"
}

check_rosetta() {
    if [[ "$(uname -m)" == "arm64" ]]; then
        if ! /usr/bin/pgrep -q oahd; then
            echo -e "${YELLOW}Warning: Rosetta 2 may not be installed.${NC}"
            echo "Running: softwareupdate --install-rosetta"
            softwareupdate --install-rosetta --agree-to-license || true
        fi
        echo -e "${GREEN}✓ Apple Silicon detected, using x86_64 emulation${NC}"
    fi
}

start_malmo_only() {
    print_banner
    echo "Starting Malmo Minecraft in Docker..."
    echo ""

    check_docker
    check_rosetta

    echo ""
    echo "Building and starting container..."
    echo "(This may take 5-10 minutes on first run)"
    echo ""

    docker compose -f docker-compose.malmo-only.yml up -d --build

    echo ""
    echo -e "${GREEN}Malmo container starting!${NC}"
    echo ""
    echo "To view logs:"
    echo "  docker compose -f deployment/docker-compose.malmo-only.yml logs -f"
    echo ""
    echo "To connect Python to Malmo:"
    echo "  export MALMO_HOST=localhost"
    echo "  export MALMO_PORT=9000"
    echo "  python test_malmo_simple.py 9000"
    echo ""
    echo "To view Minecraft via VNC (if enabled):"
    echo "  Open vnc://localhost:5900 in Finder"
    echo ""
    echo "To stop:"
    echo "  ./start_docker_malmo.sh --stop"
}

start_full_stack() {
    print_banner
    echo "Starting full Malmo stack (Minecraft + MCP Server + PostgreSQL)..."
    echo ""

    check_docker
    check_rosetta

    # Check for .env file
    if [ ! -f "../.env" ]; then
        echo -e "${YELLOW}Warning: .env file not found.${NC}"
        echo "Copy .env.example to .env and add your API keys."
    fi

    echo ""
    echo "Building and starting containers..."
    echo "(This may take 5-10 minutes on first run)"
    echo ""

    # Export env vars from .env if it exists
    if [ -f "../.env" ]; then
        export $(cat ../.env | grep -v '^#' | xargs)
    fi

    docker compose up -d --build

    echo ""
    echo -e "${GREEN}Full stack starting!${NC}"
    echo ""
    echo "Services:"
    echo "  - Malmo Minecraft: localhost:9000"
    echo "  - MCP Server:      localhost:8000"
    echo "  - PostgreSQL:      localhost:5432"
    echo ""
    echo "To view logs:"
    echo "  docker compose logs -f"
    echo ""
    echo "API docs:"
    echo "  http://localhost:8000/docs"
}

stop_containers() {
    print_banner
    echo "Stopping Malmo containers..."

    docker compose -f docker-compose.malmo-only.yml down 2>/dev/null || true
    docker compose down 2>/dev/null || true

    echo -e "${GREEN}✓ Containers stopped${NC}"
}

show_logs() {
    docker compose -f docker-compose.malmo-only.yml logs -f 2>/dev/null || \
    docker compose logs -f
}

show_help() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  (none)    Start Malmo only (for local MCP development)"
    echo "  --full    Start full stack (Malmo + MCP Server + PostgreSQL)"
    echo "  --stop    Stop all containers"
    echo "  --logs    View container logs"
    echo "  --help    Show this help"
}

# Main
case "${1:-}" in
    --full)
        start_full_stack
        ;;
    --stop)
        stop_containers
        ;;
    --logs)
        show_logs
        ;;
    --help|-h)
        show_help
        ;;
    "")
        start_malmo_only
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
