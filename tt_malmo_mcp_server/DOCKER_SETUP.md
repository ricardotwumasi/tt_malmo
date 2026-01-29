# Docker Setup for Malmo

This guide explains how to run Malmo/Minecraft in Docker on your Mac, bypassing the native macOS compatibility issues.

## Why Docker?

Running Malmo natively on macOS (especially Apple Silicon) has compatibility issues:
- LWJGL (OpenGL library) threading crashes on modern macOS
- Java 8 x86_64 requires Rosetta 2 emulation

Docker solves this by running Minecraft in a Linux container where these issues don't exist.

## Prerequisites

### 1. Install Docker Desktop

Download and install Docker Desktop for Mac:
- **Download**: https://www.docker.com/products/docker-desktop/
- **Apple Silicon**: Make sure to download the Apple Silicon version

### 2. Configure Docker for x86_64 Emulation

For Apple Silicon Macs, enable Rosetta in Docker:

1. Open Docker Desktop
2. Go to **Settings** (gear icon)
3. Go to **General**
4. Enable **"Use Rosetta for x86_64/amd64 emulation on Apple Silicon"**
5. Click **Apply & restart**

### 3. Allocate Resources

Minecraft needs adequate resources:

1. Go to **Settings** → **Resources**
2. Set:
   - **CPUs**: 4 or more
   - **Memory**: 6 GB or more
   - **Disk**: 20 GB or more
3. Click **Apply & restart**

## Quick Start

### Option 1: Malmo Only (Recommended for Development)

Run Minecraft/Malmo in Docker, MCP server locally:

```bash
cd tt_malmo_mcp_server

# Start Malmo in Docker
./start_docker_malmo.sh

# Wait for it to start (check logs)
docker compose -f deployment/docker-compose.malmo-only.yml logs -f

# In another terminal, run MCP server locally
source venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
python -m uvicorn mcp_server.server:app --reload

# Test connection
python test_malmo_simple.py 9000
```

### Option 2: Full Stack

Run everything in Docker:

```bash
cd tt_malmo_mcp_server

# Start full stack
./start_docker_malmo.sh --full

# Check logs
docker compose logs -f

# Access services
# - API: http://localhost:8000/docs
# - Malmo: localhost:9000
# - PostgreSQL: localhost:5432
```

## Commands Reference

```bash
# Start Malmo only
./start_docker_malmo.sh

# Start full stack (Malmo + MCP Server + PostgreSQL)
./start_docker_malmo.sh --full

# View logs
./start_docker_malmo.sh --logs

# Stop containers
./start_docker_malmo.sh --stop

# Manual docker compose commands
cd deployment
docker compose -f docker-compose.malmo-only.yml up -d    # Malmo only
docker compose up -d                                       # Full stack
docker compose down                                        # Stop all
```

## Viewing Minecraft (VNC)

The Docker container runs Minecraft headlessly with a virtual display. To see it:

1. VNC is enabled by default in the `docker-compose.malmo-only.yml`
2. Connect using any VNC client to `localhost:5900`
3. On Mac, open Finder and press `Cmd+K`, then enter: `vnc://localhost:5900`

## Troubleshooting

### "Docker is not running"

1. Open Docker Desktop application
2. Wait for it to fully start (icon stops animating)
3. Try again

### Build takes too long

First build downloads Minecraft assets and compiles mods. This is normal.
- First build: 5-10 minutes
- Subsequent builds: 1-2 minutes

### Port already in use

```bash
# Check what's using port 9000
lsof -i :9000

# Kill any existing Minecraft processes
pkill -f "java.*Malmo" || true

# Stop any existing containers
docker compose down
```

### Container crashes immediately

Check logs:
```bash
docker compose -f deployment/docker-compose.malmo-only.yml logs malmo
```

Common issues:
- Insufficient memory: Increase Docker memory allocation
- Missing Malmo directory: Ensure `../malmo` exists

### VNC not connecting

1. Ensure VNC is enabled: `ENABLE_VNC=true` in docker-compose
2. Try restarting the container
3. Check if port 5900 is available

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Mac (Host)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────┐     ┌────────────────────────────┐    │
│   │   MCP Server    │     │    Docker Container        │    │
│   │   (Python)      │────▶│                            │    │
│   │   Port 8000     │     │  ┌────────────────────┐   │    │
│   └─────────────────┘     │  │  Minecraft 1.11.2  │   │    │
│                           │  │  + Malmo Mod       │   │    │
│   ┌─────────────────┐     │  │  Port 9000         │   │    │
│   │   Your Python   │────▶│  └────────────────────┘   │    │
│   │   Scripts       │     │                            │    │
│   └─────────────────┘     │  ┌────────────────────┐   │    │
│                           │  │  Xvfb (Virtual     │   │    │
│                           │  │  Display)          │   │    │
│                           │  └────────────────────┘   │    │
│                           │                            │    │
│                           │  Platform: linux/amd64    │    │
│                           └────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Connecting Python to Docker Malmo

When Malmo runs in Docker, connect from your local Python:

```python
import malmoenv

env = malmoenv.make()
env.init(
    mission_xml,
    port=9000,           # Docker exposes this port
    server='localhost',  # Connect to localhost (Docker maps it)
    role=0
)

obs = env.reset()  # This now works!
```

## Next Steps

Once Docker is running:

1. **Test connection**: `python test_malmo_simple.py 9000`
2. **Run integration test**: `python test_malmo_integration.py --port 9000`
3. **Create AI agents**: Use the MCP server API at `http://localhost:8000/docs`
