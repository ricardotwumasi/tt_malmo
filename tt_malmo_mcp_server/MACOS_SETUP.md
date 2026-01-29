# macOS Local Setup Guide

This guide will help you run the Malmo MCP Server locally on macOS.

## Quick Overview

We'll set up TWO components running simultaneously:
1. **MCP Server** (Python/FastAPI) - Manages AI agents with PIANO architecture
2. **Malmo/Minecraft** (Java) - The Minecraft environment where agents live

## Prerequisites

### Install Homebrew (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Apple Silicon (M1/M2/M3/M4) Users

If you're on Apple Silicon, you need additional setup for Java 8 compatibility:

1. **Install Rosetta 2** (required for x86_64 emulation):
```bash
softwareupdate --install-rosetta --agree-to-license
```

2. **Install x86_64 Java 8** (Minecraft requires x86_64 Java):
```bash
# Install x86_64 Homebrew (if not already done)
arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Java 8 under Rosetta
arch -x86_64 /usr/local/bin/brew install --cask temurin@8
```

3. **Set JAVA_HOME for Malmo**:
```bash
# Add to your ~/.zshrc or ~/.bash_profile
export JAVA_HOME=$(/usr/libexec/java_home -v 1.8 2>/dev/null || echo "/Library/Java/JavaVirtualMachines/temurin-8.jdk/Contents/Home")
```

4. **Docker Desktop Settings** (for containerized deployment):
   - Open Docker Desktop > Settings > General
   - Enable "Use Rosetta for x86_64/amd64 emulation on Apple Silicon"
   - This allows running x86_64 containers (required for Malmo)

### Intel Mac Users

Standard installation works directly:

### Install Required Tools

```bash
# Java 8 (required for Malmo/Minecraft)
brew install --cask temurin@8

# Python 3.10+
brew install python@3.10

# Verify installations
java -version  # Should show version 1.8 or 8
python3 --version  # Should show 3.10 or higher
```

## Part 1: Configure Your API Key

### Step 1: Run the setup script

```bash
cd tt_malmo_mcp_server
./setup_api_key.sh
```

Then paste your Gemini API key when prompted.

### Step 2: Verify API key is set

```bash
cat .env | grep GOOGLE_API_KEY
# Should show: GOOGLE_API_KEY=your_actual_key_here
```

## Part 2: Setup MCP Server

### Step 1: Create Python virtual environment

```bash
cd tt_malmo_mcp_server

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Your prompt should now show (venv)
```

### Step 2: Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn (web server)
- Google Generative AI SDK (Gemini)
- Anthropic SDK (Claude, if you get a key later)
- Pydantic, asyncio, etc.

### Step 3: Test MCP Server (without Malmo for now)

```bash
# Start the server
python -m uvicorn mcp_server.server:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 4: Test in another terminal

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","active_agents":0,"connected_websockets":0}
```

Press `Ctrl+C` to stop the server for now.

## Part 3: Setup Malmo/Minecraft

### Step 1: Install Malmo Python dependencies

```bash
cd ../malmo  # Go to the malmo directory

# Install MalmoEnv (the Python interface)
pip install lxml pillow numpy gym

# On macOS, you may need to install additional dependencies
pip install malmoenv
```

### Step 2: Build Malmo (Required for first-time setup)

```bash
cd Minecraft

# This script builds the Malmo mod
./gradlew setupDecompWorkspace
./gradlew build

# This may take 5-15 minutes the first time
```

### Step 3: Launch Minecraft with Malmo

**Terminal 1** - Launch Minecraft client:

```bash
cd /Users/k1812261/claude_code/tt_project_malmo/malmo/Minecraft

# Launch Minecraft
./launchClient.sh
```

This will:
1. Download Minecraft if needed
2. Start Minecraft with the Malmo mod loaded
3. Open the Minecraft window

**What you should see:**
- Minecraft launcher opens
- Game loads with "Malmo Mod" in the mods list
- You'll see the Minecraft main menu

### Step 4: Test Malmo with a simple mission

**Terminal 2** - Run a test mission:

```bash
cd /Users/k1812261/claude_code/tt_project_malmo/malmo/MalmoEnv

# Run a simple test
python3 -c "
import malmoenv
env = malmoenv.make()
env.reset()
print('Malmo is working!')
env.close()
"
```

If successful, you should see:
- Minecraft loads a world
- The screen might flash/change
- Terminal prints "Malmo is working!"

## Part 4: Run MCP Server + Malmo Together

Now let's run everything together!

### Terminal 1: Start Minecraft/Malmo

```bash
cd /Users/k1812261/claude_code/tt_project_malmo/malmo/Minecraft
./launchClient.sh

# Wait for Minecraft to fully load to main menu
```

### Terminal 2: Start MCP Server

```bash
cd /Users/k1812261/claude_code/tt_project_malmo/tt_malmo_mcp_server
source venv/bin/activate
python -m uvicorn mcp_server.server:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 3: Create a test agent

```bash
# Create a Gemini agent
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Explorer_Gemini",
    "llm_type": "gemini",
    "role": 0,
    "traits": ["curious", "adventurous"]
  }'

# Save the agent_id from the response
# It will look like: {"agent_id":"550e8400-e29b-41d4-a716-446655440000", ...}
```

Copy the `agent_id`, then start the agent:

```bash
# Replace AGENT_ID with your actual ID
curl -X POST http://localhost:8000/agents/AGENT_ID/start
```

### Terminal 4: Monitor agent logs

```bash
# Watch MCP server logs in Terminal 2
# You should see output like:

# [Explorer_Gemini] Decision: explore - Looking for interesting features
# [Explorer_Gemini] Goal Generated: Find resources to gather
# Action Awareness: Waiting for action result...
```

## Part 5: Verify Everything is Working

### Check 1: MCP Server Status

```bash
curl http://localhost:8000/health
# {"status":"healthy","active_agents":1,"connected_websockets":0}

curl http://localhost:8000/agents
# Shows list of created agents
```

### Check 2: Agent PIANO Architecture

Look at Terminal 2 (MCP server logs). You should see evidence of PIANO modules running:

```
Started PIANO architecture for agent: Explorer_Gemini
[Explorer_Gemini] perception module processing...
[Explorer_Gemini] social_awareness module processing...
[Explorer_Gemini] goal_generation generating new goal...
[Explorer_Gemini] Decision: explore - Searching for resources
```

### Check 3: Minecraft Status

- Minecraft should be running
- You can see the main menu or world
- No error messages in the Minecraft console

## Troubleshooting

### Issue: "Port 8000 already in use"

```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
python -m uvicorn mcp_server.server:app --port 8001
```

### Issue: "Java version error"

```bash
# Check Java version
java -version

# If not version 8, set JAVA_HOME
export JAVA_HOME=$(/usr/libexec/java_home -v 1.8)

# Apple Silicon: If Java 8 not found, install x86_64 version
arch -x86_64 /usr/local/bin/brew install --cask temurin@8
```

### Issue: "Docker build fails on Apple Silicon"

```bash
# Ensure Rosetta is enabled in Docker Desktop
# Settings > General > "Use Rosetta for x86_64/amd64 emulation"

# Or build explicitly for amd64
docker build --platform linux/amd64 -f deployment/Dockerfile.malmo .
```

### Issue: "Malmo mod not loading"

```bash
cd /Users/k1812261/claude_code/tt_project_malmo/malmo/Minecraft

# Rebuild
./gradlew clean build

# Then try launching again
./launchClient.sh
```

### Issue: "google.generativeai module not found"

```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall
pip install --upgrade google-generativeai
```

### Issue: "API key invalid"

```bash
# Re-run setup script
cd tt_malmo_mcp_server
./setup_api_key.sh

# Verify it's set
cat .env | grep GOOGLE
```

## What's Next?

Once everything is running:

1. **Create multiple agents** with different traits
2. **Generate a mission** using the mission builder
3. **Watch agents interact** in the Minecraft world
4. **Implement the Environment Manager** to connect agents to Malmo

See `QUICKSTART.md` for more advanced testing.

## Useful Commands

```bash
# Activate Python environment
cd tt_malmo_mcp_server && source venv/bin/activate

# Start MCP server
python -m uvicorn mcp_server.server:app --reload

# Start Minecraft
cd ../malmo/Minecraft && ./launchClient.sh

# Create agent
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{"name":"TestAgent","llm_type":"gemini","role":0}'

# List agents
curl http://localhost:8000/agents

# Check health
curl http://localhost:8000/health
```

## Architecture Diagram (Local Setup)

```
┌─────────────────────────────────────────┐
│  Terminal 1: Minecraft + Malmo          │
│  Port: 9000-9010                        │
│  ./launchClient.sh                      │
└────────────────┬────────────────────────┘
                 │
                 │ (Not yet connected)
                 │
┌────────────────▼────────────────────────┐
│  Terminal 2: MCP Server                 │
│  Port: 8000                             │
│  PIANO Architecture                     │
│  Gemini 2.5 Flash Lite API              │
│  python -m uvicorn mcp_server.server:app│
└────────────────┬────────────────────────┘
                 │
                 │ REST API / WebSocket
                 │
┌────────────────▼────────────────────────┐
│  Terminal 3: API Calls                  │
│  curl http://localhost:8000/...         │
│  Create agents, start/stop, monitor     │
└─────────────────────────────────────────┘
```

---

**Status**: Ready for local testing
**Next Step**: Implement Environment Manager to connect agents to Malmo
