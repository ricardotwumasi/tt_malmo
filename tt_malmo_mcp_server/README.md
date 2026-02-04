# Malmo MCP Server with PIANO Architecture

Multi-agent benchmarking system using Project Malmo, Model Context Protocol (MCP), and PIANO (Parallel Information Aggregation via Neural Orchestration) architecture.

## Overview

This system enables multiple LLM agents (Claude Opus 4.5, Gemini 2.5 Flash, Ollama/Qwen) to interact with Minecraft through Project Malmo, using the PIANO architecture for cognitive processing. Designed for deployment on King's College London CREATE Cloud infrastructure.

## Architecture Components

1. **MCP Server** - FastAPI server coordinating multiple agents
2. **PIANO Architecture** - Cognitive processing with 5 concurrent modules
3. **Malmo Integration** - Environment manager bridging agents to Minecraft
4. **LLM Adapters** - Support for multiple LLMs (Gemini, Claude, Ollama, local models)
5. **Mission Control** - Start/stop agents in Minecraft world

## Quick Start (Windows)

### Startup Sequence

```powershell
# Terminal 1: Start Ollama LLM backend
.\start_ollama.bat

# Terminal 2: Start MCP Server
.\start_server.bat

# Terminal 3: Start Minecraft with Malmo
cd malmo\Minecraft && .\launchClient.bat -port 9000 -env

# Terminal 4: Start Dashboard
.\start_dashboard.bat

# Terminal 5: Spawn agents in Minecraft (after agents are running)
.\start_mission.bat
```

### API Endpoints for Mission Control

```powershell
# Start mission - spawns all running agents in Minecraft
curl -X POST http://localhost:8080/mission/start

# Check mission status
curl http://localhost:8080/mission/status

# Stop mission - returns agents to thinking-only mode
curl -X POST http://localhost:8080/mission/stop
```

## Connecting Agents to Minecraft

The system bridges PIANO architecture agents to actual Minecraft characters:

```
Agent (PIANO) -> Decisions -> MalmoEnv -> Minecraft -> Visible Actions
```

When a mission is started:
1. Running agents are fetched from MCP server
2. Multi-agent mission XML is generated
3. Each agent connects to Malmo on sequential ports (9000, 9001, 9002...)
4. Agent decisions are translated to Malmo commands
5. Minecraft observations are fed back to agent state

### Building Actions

Agents can perform building actions:
- `place` / `build` - Places block in front of agent
- `mine` / `break` / `dig` - Mines/destroys block
- `select_slot_N` - Selects hotbar slot N
- `craft_ITEM` - Crafts specified item
- `move`, `turn`, `jump` - Movement commands

## Architecture

### CREATE Cloud Deployment

1. Create Ubuntu 20.04 VM on CREATE Cloud (8GB RAM, 4 vCPUs)
2. Install Docker and Docker Compose
3. Clone repository and configure .env with API keys
4. Run: `docker-compose up -d`
5. Access at: `http://your-vm-ip:8000`

### Local Development (Linux/macOS)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000
```

## Files

| File | Purpose |
|------|---------|
| `start_server.bat` | Launch MCP server |
| `start_dashboard.bat` | Launch Streamlit dashboard |
| `start_mission.bat` | Spawn agents in Minecraft |
| `stop_mission.bat` | Disconnect agents from Minecraft |
| `launch_multi_agent.py` | Python script for mission control |

## Documentation

- Full deployment guide: DEPLOY.md
- Windows deployment: WINDOWS_DEPLOYMENT.md
- API documentation: http://localhost:8080/docs
- CREATE Cloud docs: https://docs.er.kcl.ac.uk/CREATE/

## Contact

- GitHub: https://github.com/ricardotwumasi/tt_malmo
- CREATE Support: support@er.kcl.ac.uk
