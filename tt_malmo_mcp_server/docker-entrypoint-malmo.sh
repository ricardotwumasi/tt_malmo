#!/bin/bash
# Entrypoint for Malmo server container

set -e

# Start virtual display
echo "Starting virtual display..."
Xvfb :99 -screen 0 1024x768x24 &
sleep 2

# Start window manager
fluxbox &
sleep 1

# Set display
export DISPLAY=:99

# Get port from environment or default
MALMO_PORT=${MALMO_PORT:-9000}

echo "Starting Malmo server on port $MALMO_PORT..."

# Navigate to Malmo directory
cd /app/malmo/Minecraft

# Launch Minecraft with Malmo mod
exec ./launchClient.sh -port $MALMO_PORT -env
