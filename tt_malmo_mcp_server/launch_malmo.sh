#!/bin/bash
# Launch Malmo Minecraft client on Apple Silicon
#
# Usage: ./launch_malmo.sh [port]
#   port: Malmo port (default: 9000)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MINECRAFT_DIR="$(dirname "$SCRIPT_DIR")/malmo/Minecraft"

# Set Java 8
export JAVA_HOME="/Library/Java/JavaVirtualMachines/temurin-8.jdk/Contents/Home"

# Default port
PORT=${1:-9000}

echo "=============================================="
echo "  Starting Malmo Minecraft"
echo "=============================================="
echo "  Port: $PORT"
echo "  Java: $JAVA_HOME"
echo ""
echo "  Press Ctrl+C to stop."
echo "=============================================="
echo ""

cd "$MINECRAFT_DIR"

# Use the standard launchClient.sh approach with port and env flags
arch -x86_64 ./launchClient.sh -port $PORT -env
