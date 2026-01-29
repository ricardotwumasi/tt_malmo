#!/bin/bash
# =============================================================================
# Malmo MCP Server Deployment Script
# =============================================================================
#
# Quick deployment script for Linux servers.
#
# Usage:
#   ./deploy.sh              # Deploy with Docker
#   ./deploy.sh --local      # Deploy without Docker
#   ./deploy.sh --help       # Show help
#
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_banner() {
    echo ""
    echo "=============================================="
    echo "  Malmo MCP Server Deployment"
    echo "=============================================="
    echo ""
}

check_requirements() {
    echo "Checking requirements..."

    # Check Python
    if command -v python3.11 &> /dev/null; then
        echo -e "${GREEN}✓ Python 3.11 found${NC}"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ "$PYTHON_VERSION" == "3.10" ]] || [[ "$PYTHON_VERSION" == "3.11" ]] || [[ "$PYTHON_VERSION" == "3.12" ]]; then
            echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
        else
            echo -e "${YELLOW}⚠ Python $PYTHON_VERSION found (3.10+ recommended)${NC}"
        fi
    else
        echo -e "${RED}✗ Python 3 not found${NC}"
        exit 1
    fi

    # Check Docker (if not --local)
    if [ "$1" != "--local" ]; then
        if command -v docker &> /dev/null; then
            echo -e "${GREEN}✓ Docker found${NC}"
        else
            echo -e "${YELLOW}⚠ Docker not found - install it or use --local${NC}"
        fi
    fi

    echo ""
}

setup_env() {
    echo "Setting up environment..."

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${YELLOW}Created .env from .env.example${NC}"
            echo -e "${YELLOW}Please edit .env and add your API keys${NC}"
            echo ""
            read -p "Press Enter after editing .env, or Ctrl+C to exit..."
        else
            echo -e "${RED}✗ No .env.example found${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ .env file exists${NC}"
    fi

    # Verify API keys
    if grep -q "GOOGLE_API_KEY=your" .env 2>/dev/null; then
        echo -e "${YELLOW}⚠ GOOGLE_API_KEY appears to be placeholder${NC}"
    fi

    echo ""
}

deploy_docker() {
    print_banner
    echo "Deploying with Docker..."
    echo ""

    check_requirements
    setup_env

    # Load env vars
    export $(cat .env | grep -v '^#' | xargs)

    echo "Starting services..."
    docker compose -f deployment/docker-compose.yml up -d --build

    echo ""
    echo -e "${GREEN}Deployment complete!${NC}"
    echo ""
    echo "Services:"
    echo "  - MCP Server: http://localhost:8000"
    echo "  - API Docs:   http://localhost:8000/docs"
    echo ""
    echo "Commands:"
    echo "  - View logs:  docker compose -f deployment/docker-compose.yml logs -f"
    echo "  - Stop:       docker compose -f deployment/docker-compose.yml down"
}

deploy_local() {
    print_banner
    echo "Deploying locally (without Docker)..."
    echo ""

    check_requirements --local

    # Create venv if needed
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    echo "Activating virtual environment..."
    source venv/bin/activate

    echo "Installing dependencies..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q

    setup_env

    # Load env vars
    export $(cat .env | grep -v '^#' | xargs)

    echo "Running tests..."
    pytest tests/ -v --tb=short 2>/dev/null || echo "Some tests may have failed"

    echo ""
    echo "Starting MCP Server..."
    echo ""
    python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000
}

show_help() {
    echo "Malmo MCP Server Deployment Script"
    echo ""
    echo "Usage:"
    echo "  ./deploy.sh              Deploy with Docker (recommended)"
    echo "  ./deploy.sh --local      Deploy without Docker"
    echo "  ./deploy.sh --help       Show this help"
    echo ""
    echo "Requirements:"
    echo "  - Python 3.10+ (for --local)"
    echo "  - Docker (for default deployment)"
    echo "  - At least one LLM API key in .env"
}

# Main
case "${1:-}" in
    --local)
        deploy_local
        ;;
    --help|-h)
        show_help
        ;;
    "")
        deploy_docker
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
