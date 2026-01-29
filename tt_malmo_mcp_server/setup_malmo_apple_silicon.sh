#!/bin/bash
# =============================================================================
# Malmo Setup Script for Apple Silicon Macs (M1/M2/M3/M4)
# =============================================================================
#
# This script sets up Malmo/Minecraft on Apple Silicon using Rosetta 2
# for x86_64 Java 8 compatibility.
#
# Usage: ./setup_malmo_apple_silicon.sh
# =============================================================================

set -e  # Exit on error

echo "=============================================="
echo "  Malmo Setup for Apple Silicon"
echo "=============================================="
echo ""

# Check if running on Apple Silicon
ARCH=$(uname -m)
if [ "$ARCH" != "arm64" ]; then
    echo "Warning: This script is designed for Apple Silicon (arm64)."
    echo "Detected architecture: $ARCH"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# =============================================================================
# Step 1: Install Rosetta 2
# =============================================================================
echo ""
echo "[Step 1/5] Checking Rosetta 2..."

if /usr/bin/pgrep -q oahd; then
    echo "  Rosetta 2 is already installed."
else
    echo "  Installing Rosetta 2..."
    softwareupdate --install-rosetta --agree-to-license
    echo "  Rosetta 2 installed."
fi

# =============================================================================
# Step 2: Check/Install Java 8 (x86_64)
# =============================================================================
echo ""
echo "[Step 2/5] Checking Java 8 (x86_64)..."

# Check if x86_64 Java 8 exists
JAVA8_PATH="/Library/Java/JavaVirtualMachines/temurin-8.jdk/Contents/Home"
if [ -d "$JAVA8_PATH" ]; then
    echo "  Java 8 found at: $JAVA8_PATH"
else
    echo "  Java 8 not found. Installing via Homebrew (x86_64)..."

    # Check if x86_64 Homebrew exists
    if [ ! -f "/usr/local/bin/brew" ]; then
        echo "  Installing x86_64 Homebrew..."
        arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    # Install Java 8 via x86_64 Homebrew
    echo "  Installing Temurin Java 8..."
    arch -x86_64 /usr/local/bin/brew install --cask temurin@8

    echo "  Java 8 installed."
fi

# Set JAVA_HOME
export JAVA_HOME="$JAVA8_PATH"
echo "  JAVA_HOME set to: $JAVA_HOME"

# Verify Java version
echo "  Java version:"
arch -x86_64 $JAVA_HOME/bin/java -version 2>&1 | head -3

# =============================================================================
# Step 3: Setup Malmo/Minecraft
# =============================================================================
echo ""
echo "[Step 3/5] Setting up Malmo..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MALMO_DIR="$(dirname "$SCRIPT_DIR")/malmo"
MINECRAFT_DIR="$MALMO_DIR/Minecraft"

if [ ! -d "$MALMO_DIR" ]; then
    echo "  Error: Malmo directory not found at $MALMO_DIR"
    echo "  Please clone Malmo first:"
    echo "    git clone https://github.com/microsoft/malmo.git ../malmo"
    exit 1
fi

echo "  Malmo directory: $MALMO_DIR"

# Create version.properties
cd "$MINECRAFT_DIR"
if [ -f "../VERSION" ]; then
    echo -n "malmomod.version=" > ./src/main/resources/version.properties
    cat ../VERSION >> ./src/main/resources/version.properties
    echo "  Created version.properties"
fi

# =============================================================================
# Step 4: Build Minecraft with Malmo Mod
# =============================================================================
echo ""
echo "[Step 4/5] Building Minecraft with Malmo mod..."
echo "  This may take 5-15 minutes on first run..."

cd "$MINECRAFT_DIR"

# Set Gradle to use Java 8
export JAVA_HOME="$JAVA8_PATH"

# Build using Rosetta for x86_64
echo "  Running: gradlew setupDecompWorkspace"
arch -x86_64 ./gradlew setupDecompWorkspace --no-daemon

echo "  Running: gradlew build"
arch -x86_64 ./gradlew build --no-daemon

echo "  Build complete!"

# =============================================================================
# Step 5: Install MalmoEnv
# =============================================================================
echo ""
echo "[Step 5/5] Installing MalmoEnv Python package..."

cd "$SCRIPT_DIR"
source venv/bin/activate 2>/dev/null || {
    echo "  Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
}

pip install gymnasium lxml numpy pillow

# Install MalmoEnv from local directory
cd "$MALMO_DIR/MalmoEnv"
pip install -e .

echo "  MalmoEnv installed."

# =============================================================================
# Create launch script
# =============================================================================
echo ""
echo "Creating launch helper script..."

cat > "$SCRIPT_DIR/launch_malmo.sh" << 'LAUNCH_EOF'
#!/bin/bash
# Launch Malmo Minecraft client on Apple Silicon

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MINECRAFT_DIR="$(dirname "$SCRIPT_DIR")/malmo/Minecraft"

# Set Java 8
export JAVA_HOME="/Library/Java/JavaVirtualMachines/temurin-8.jdk/Contents/Home"

# Default port
PORT=${1:-9000}

echo "Starting Malmo Minecraft on port $PORT..."
echo "Press Ctrl+C to stop."
echo ""

cd "$MINECRAFT_DIR"
arch -x86_64 ./gradlew runClient -Pport=$PORT -Penv=true --no-daemon
LAUNCH_EOF

chmod +x "$SCRIPT_DIR/launch_malmo.sh"
echo "  Created: launch_malmo.sh"

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""
echo "To run Malmo with AI agents:"
echo ""
echo "Terminal 1 - Start Minecraft:"
echo "  cd $SCRIPT_DIR"
echo "  ./launch_malmo.sh 9000"
echo ""
echo "Terminal 2 - Start MCP Server:"
echo "  cd $SCRIPT_DIR"
echo "  source venv/bin/activate"
echo "  export \$(cat .env | grep -v '^#' | xargs)"
echo "  python -m uvicorn mcp_server.server:app --reload"
echo ""
echo "Terminal 3 - Create and test agents:"
echo "  curl -X POST http://localhost:8000/agents \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"name\":\"TestAgent\",\"llm_type\":\"gemini\",\"role\":0}'"
echo ""
echo "For integration test, run:"
echo "  python test_malmo_integration.py"
echo ""
