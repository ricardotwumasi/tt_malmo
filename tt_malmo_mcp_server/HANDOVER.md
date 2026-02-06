# Malmo MCP Server - Developer Handover Document

**Date:** January 2025
**Project:** Multi-Agent AI Benchmarking System with PIANO Architecture
**Repository:** https://github.com/ricardotwumasi/tt_malmo
**Contact:** ricardo.twumasi@kcl.ac.uk

---

## Executive Summary

This project implements a multi-agent AI benchmarking system using Microsoft Project Malmo (Minecraft) as the evaluation environment. The system uses the PIANO (Parallel Information Aggregation via Neural Orchestration) cognitive architecture to coordinate multiple AI agents powered by various LLM providers (Gemini, OpenRouter, Cerebras, Cloudflare, **Local MLX**).

**Current Status:** MVP 85% complete - local LLM tested, Linux VM setup in progress.

---

## Quick Start for New Developers

### 1. Clone the Repository (with Malmo submodule)

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/ricardotwumasi/tt_malmo.git
cd tt_malmo

# If already cloned without submodules:
git submodule update --init --recursive
```

### 2. Set Up Development Environment

```bash
cd tt_malmo_mcp_server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and add at least one API key (GOOGLE_API_KEY recommended)
```

### 3. Run the MCP Server

```bash
export $(cat .env | grep -v '^#' | xargs)
python -m uvicorn mcp_server.server:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Create an agent
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{"name":"TestAgent","llm_type":"gemini","role":0,"traits":["curious"]}'

# List agents
curl http://localhost:8000/agents
```

---

## Current Implementation Status

### Completed Components

| Component | Status | Location |
|-----------|--------|----------|
| **MCP Server** | Complete | `mcp_server/` |
| **PIANO Architecture** | Complete (5 modules) | `piano_architecture/` |
| **LLM Adapters** | Complete (5 providers) | `llm_adapters/` |
| **Malmo Integration** | Complete | `malmo_integration/` |
| **Benchmarking Framework** | Complete | `benchmarking/` |
| **Test Suite** | Complete (95+ tests) | `tests/` |
| **Docker Configuration** | Complete | `deployment/` |
| **Documentation** | Complete | Various .md files |

### LLM Providers Supported

| Provider | Model | Free Tier | Status |
|----------|-------|-----------|--------|
| **Local MLX** | Qwen2.5-1.5B-Instruct-4bit | Free (on-device) | **Tested (12K decisions)** |
| **Google Gemini** | gemini-2.5-flash-lite | Yes (15 RPM) | Tested |
| **OpenRouter** | DeepSeek, GLM, Llama | Yes (varies) | Implemented |
| **Cerebras** | Llama 3.1/3.3 | Yes (1M tokens/day) | Implemented |
| **Cloudflare** | Llama, DeepSeek | Yes (10K neurons/day) | Implemented |
| **Anthropic Claude** | Claude Opus 4.5 | No (paid) | Implemented |

### PIANO Cognitive Modules

1. **Perception** - Processes sensory input from Minecraft
2. **Social Awareness** - Tracks relationships with other agents
3. **Goal Generation** - Creates and prioritizes goals
4. **Action Awareness** - Monitors action outcomes (prevents hallucinations)
5. **Memory Consolidation** - Manages working/long-term memory

---

## Project Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (FastAPI)                      │
│  - REST API: /agents, /agents/{id}/start, /health           │
│  - WebSocket: Real-time agent updates                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              PIANO Architecture                      │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │Perception│ │ Social  │ │  Goal   │ │ Action  │   │   │
│  │  │         │ │Awareness│ │  Gen    │ │Awareness│   │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │   │
│  │       │           │           │           │         │   │
│  │       └───────────┴─────┬─────┴───────────┘         │   │
│  │                         ▼                           │   │
│  │              ┌─────────────────────┐                │   │
│  │              │ Cognitive Controller │◄── LLM        │   │
│  │              │    (Bottleneck)      │   Adapter     │   │
│  │              └─────────────────────┘                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Malmo / Minecraft     │
              │   (via MalmoEnv)        │
              └─────────────────────────┘
```

---

## Repository Structure

```
tt_malmo/
├── malmo/                          # Microsoft Malmo (git submodule)
│   ├── MalmoEnv/                   # Python environment interface
│   ├── Minecraft/                  # Modified Minecraft client
│   └── sample_missions/            # Example mission XMLs
│
├── tt_malmo_mcp_server/            # Main application
│   ├── mcp_server/                 # FastAPI server
│   │   ├── server.py               # API endpoints
│   │   ├── agent_manager.py        # Agent lifecycle
│   │   └── protocol/               # Message types
│   │
│   ├── piano_architecture/         # PIANO cognitive modules
│   │   ├── cognitive_controller.py # Decision bottleneck
│   │   ├── agent_state.py          # Shared state
│   │   └── modules/                # 5 cognitive modules
│   │
│   ├── llm_adapters/               # LLM provider integrations
│   │   ├── factory.py              # Adapter factory
│   │   ├── local_adapter.py        # Local MLX (Apple Silicon)
│   │   ├── gemini_adapter.py       # Google Gemini
│   │   ├── openrouter_adapter.py   # OpenRouter (multi-model)
│   │   ├── cerebras_adapter.py     # Cerebras
│   │   └── cloudflare_adapter.py   # Cloudflare Workers AI
│   │
│   ├── malmo_integration/          # Malmo/Minecraft bridge
│   │   ├── environment_manager.py  # Environment connection
│   │   └── mission_builder.py      # Mission XML generation
│   │
│   ├── benchmarking/               # Metrics and evaluation
│   │   ├── metrics_store.py        # PostgreSQL/in-memory storage
│   │   └── evaluator.py            # Benchmark scoring
│   │
│   ├── deployment/                 # Docker configurations
│   │   ├── docker-compose.yml      # Full stack
│   │   ├── Dockerfile.mcp_server   # MCP server container
│   │   └── Dockerfile.malmo        # Malmo container
│   │
│   ├── tests/                      # Test suite (95+ tests)
│   │   ├── test_piano_modules.py
│   │   ├── test_mcp_server.py
│   │   ├── test_gemini_adapter.py
│   │   └── ...
│   │
│   ├── config.py                   # Configuration management
│   ├── requirements.txt            # Python dependencies
│   └── .env.example                # Environment template
│
├── README.md                       # Project overview
├── CHANGELOG.md                    # Version history
├── PROJECT_STATUS.md               # Development status
└── .gitmodules                     # Submodule configuration
```

---

## Pending Development Tasks

### Priority 1: Complete Linux VM Setup (In Progress)

**Goal:** Finish UTM Linux VM configuration and connect agents to Minecraft.

**Current Status:** Ubuntu 22.04 ARM64 installed, desktop environment pending.

**Remaining Steps:**
1. Install XFCE desktop and lightdm
2. Reboot into graphical environment
3. Clone repository and build Malmo
4. Launch Minecraft and verify connection
5. Run agents from host Mac

**Documentation:** See "Linux VM Setup (UTM)" section below

### Priority 2: Deploy on CREATE Cloud

**Goal:** Get the full benchmark running on CREATE Cloud for production.

**Steps:**
1. Request CREATE Cloud VM (Ubuntu 22.04, 8GB RAM)
2. Clone repository with submodules
3. Run `./deploy.sh` for Docker deployment
4. Test with 5-10 agents

**Documentation:** See `LINUX_DEPLOYMENT.md`

### Priority 3: Complete Minecraft Integration Testing

**Goal:** Verify agents can control Minecraft via MalmoEnv.

**Current Issue:** macOS has LWJGL threading compatibility issues. Use Linux VM or Docker.

**Steps:**
1. Deploy on Linux (VM or Docker)
2. Start Minecraft with Malmo mod
3. Connect agents via environment manager
4. Verify action execution

### Priority 3: Implement Evaluation Metrics Collection

**Goal:** Collect and store benchmark metrics for analysis.

**Components to integrate:**
- `benchmarking/metrics_store.py` - Already implemented
- `benchmarking/evaluator.py` - Already implemented
- Need: Connect to PIANO decision loop

**Metrics domains:**
- Alignment: Goal adherence, ethical behavior
- Autonomy: Independent decision-making
- Performance: Task completion, resource gathering
- Social: Multi-agent cooperation

### Priority 4: Build Web Dashboard

**Goal:** Real-time visualization of agent performance.

**Suggested approach:**
- Streamlit dashboard for quick development
- Connect to metrics store
- Display agent states, decisions, scores

---

## Configuration Reference

### Environment Variables (.env)

```bash
# LLM API Keys (at least one required)
GOOGLE_API_KEY=your_gemini_key           # Recommended - free tier
OPENROUTER_API_KEY=your_openrouter_key   # Access to many models
CEREBRAS_API_KEY=your_cerebras_key       # Fast inference
CLOUDFLARE_API_TOKEN=your_cf_token       # Reliable infrastructure
ANTHROPIC_API_KEY=your_anthropic_key     # Premium option

# Database (optional - uses in-memory if not set)
DATABASE_URL=postgresql://user:pass@localhost:5432/malmo_benchmarks

# Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MALMO_HOST=localhost
MALMO_PORT=9000
```

### Key Configuration Files

| File | Purpose |
|------|---------|
| `.env` | API keys, secrets (not in git) |
| `.env.example` | Template for .env |
| `config.py` | Centralized configuration |
| `requirements.txt` | Python dependencies |
| `pytest.ini` | Test configuration |

---

## API Reference

### Agent Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server health check |
| `/agents` | GET | List all agents |
| `/agents` | POST | Create new agent |
| `/agents/{id}` | GET | Get agent details |
| `/agents/{id}` | DELETE | Delete agent |
| `/agents/{id}/start` | POST | Start agent PIANO loop |
| `/agents/{id}/stop` | POST | Stop agent |

### Create Agent Request

```json
{
  "name": "Explorer",
  "llm_type": "gemini",
  "role": 0,
  "traits": ["curious", "cautious"]
}
```

### Agent Response

```json
{
  "agent_id": "uuid-here",
  "name": "Explorer",
  "llm_type": "gemini",
  "status": "running",
  "created_at": "2025-01-29T12:00:00Z"
}
```

---

## Testing

### Run Full Test Suite

```bash
cd tt_malmo_mcp_server
source venv/bin/activate
pytest tests/ -v
```

### Run with Coverage

```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

### Test Categories

- `test_piano_modules.py` - PIANO architecture tests
- `test_mcp_server.py` - API endpoint tests
- `test_gemini_adapter.py` - Gemini LLM tests
- `test_openrouter_adapter.py` - OpenRouter tests
- `test_mission_builder.py` - Mission XML generation
- `test_environment_manager.py` - Malmo connection tests

---

## Known Issues and Workarounds

### 1. macOS Minecraft Compatibility

**Issue:** LWJGL threading crash on macOS
**Workaround:** Use Docker on Linux for Minecraft

### 2. Malmo Asset Download

**Issue:** Minecraft 1.11.2 asset servers sometimes fail
**Workaround:** Non-critical (audio/language files), can continue

### 3. Rate Limiting

**Issue:** Free LLM tiers have rate limits
**Workaround:** Use multiple providers, implement retry logic

---

## Local LLM (Apple Silicon)

### Overview

The `local` LLM provider uses **MLX** (Apple's ML framework) for fully on-device inference on Apple Silicon Macs. No API calls or internet required.

### Configuration

- **Model:** `mlx-community/Qwen2.5-1.5B-Instruct-4bit` (~1GB download, ~1.5GB RAM)
- **Framework:** MLX + mlx-lm
- **Requirements:** Apple Silicon Mac (M1/M2/M3/M4)

### Key Files

| File | Purpose |
|------|---------|
| `llm_adapters/local_adapter.py` | LocalAdapter class with async MLX inference |
| `llm_adapters/factory.py` | Updated with 'local' provider support |

### Technical Details

```python
# Chat template (Qwen ChatML format)
<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
```

**Threading:** Uses `threading.Lock()` to serialize GPU operations (Metal safety)

**Caching:** Models cached at `~/hf_cache/` (HF_HOME environment variable)

### Test Results (January 2025)

Two agents ran successfully for extended testing:
- **LocalExplorer:** 5,993 decisions
- **LocalBuilder:** 5,988 decisions
- **Total:** ~12,000 decisions with no crashes

---

## Linux VM Setup (UTM)

For running Minecraft/Malmo on Apple Silicon, use a Linux VM via UTM.

### 1. Install UTM

Download from: https://mac.getutm.app/ or `brew install --cask utm`

### 2. Create Ubuntu VM

1. Open UTM → Create New VM → Virtualize
2. Select **Linux**
3. Download Ubuntu 22.04 ARM64 Server:
   ```bash
   curl -L -o ~/Downloads/ubuntu-22.04-arm64.iso \
     "https://cdimage.ubuntu.com/releases/22.04/release/ubuntu-22.04.5-live-server-arm64.iso"
   ```
4. Configure VM:
   - **RAM:** 8192 MB
   - **CPU Cores:** 4
   - **Storage:** 64 GB
   - **Hardware OpenGL:** Enabled (tick)
   - **Open VM settings:** Tick

5. Boot and install Ubuntu:
   - Username/Password: `malmo` / `malmo`
   - Install OpenSSH Server: Yes
   - Featured snaps: Skip all

### 3. Post-Install Configuration

After reboot, at the console:

```bash
# 1. Get IPv4 address
sudo dhclient enp0s1

# 2. Update and install desktop + Java 8
sudo apt update && sudo apt install -y xfce4 xfce4-goodies lightdm openjdk-8-jdk git

# 3. Enable display manager
sudo systemctl enable lightdm

# 4. Reboot into desktop
sudo reboot
```

### 4. Install Malmo in VM

```bash
# Clone project
git clone --recurse-submodules https://github.com/ricardotwumasi/tt_malmo.git
cd tt_malmo/malmo

# Build Minecraft client
cd Minecraft
./gradlew build

# Launch Minecraft with Malmo
./launchClient.sh -port 9000
```

### 5. Connect from Host Mac

```bash
# Find VM IP
ssh malmo@<vm-ip> "hostname -I"

# Update .env on host
MALMO_HOST=<vm-ip>
MALMO_PORT=9000

# Run agents
python run_demo.py --llm local --port 9000
```

---

## Deployment Options

### Option 1: Docker (Recommended)

```bash
cd tt_malmo_mcp_server
./deploy.sh
```

### Option 2: Local Development

```bash
cd tt_malmo_mcp_server
./deploy.sh --local
```

### Option 3: Manual

```bash
cd tt_malmo_mcp_server
source venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000
```

---

## Resources

### Documentation in Repository

- `README.md` - Project overview and quick start
- `LINUX_DEPLOYMENT.md` - Linux server deployment
- `DOCKER_SETUP.md` - Docker configuration guide
- `QUICKSTART_APPLE_SILICON.md` - macOS M1/M2/M3 setup
- `MACOS_SETUP.md` - General macOS setup
- `CHANGELOG.md` - Version history
- `PROJECT_STATUS.md` - Development status

### External Resources

- [Microsoft Malmo](https://github.com/microsoft/malmo)
- [MalmoEnv Documentation](https://github.com/microsoft/malmo/tree/master/MalmoEnv)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Gemini API](https://ai.google.dev/)
- [OpenRouter API](https://openrouter.ai/docs)

### Research Papers

- PIANO Architecture: Altera's Project Sid
- MACHIAVELLI Benchmark: https://arxiv.org/abs/2304.03279
- World Models: https://arxiv.org/abs/1803.10122

---

## Contact

**Primary:** ricardo.twumasi@kcl.ac.uk
**GitHub Issues:** https://github.com/ricardotwumasi/tt_malmo/issues
**CREATE Support:** support@er.kcl.ac.uk

---

## Handover Checklist

For the receiving developer:

- [ ] Successfully clone repository with submodules
- [ ] Set up local development environment (arm64 venv on Apple Silicon)
- [ ] Run test suite (all tests pass)
- [ ] Start MCP server locally
- [ ] Create and list agents via API
- [ ] Understand PIANO architecture
- [ ] Review pending tasks above
- [ ] Test local LLM adapter (Apple Silicon only)
- [ ] Set up Linux VM for Minecraft (see UTM section)
- [ ] Access to API keys (Gemini recommended, or use local)

---

**Last Updated:** 2026-02-05
**Version:** 2.3

### Changelog
- **2.3** (2026-02-05): City Building Benchmark tested extensively. Major stability fixes. Death/respawn still needs work.
- **2.2** (2026-02-03): Windows deployment on NVIDIA L40S VM (see below)
- **2.1** (2025-01-30): Added Local LLM (MLX) adapter, UTM Linux VM setup guide, test results
- **2.0** (2025-01-29): Initial comprehensive handover document

---

## Windows Deployment Update (February 2026)

### Current Environment
- **Machine:** er-prj-393-vm02.kclad.ds.kcl.ac.uk
- **GPU:** NVIDIA L40S (46GB VRAM) - verified working
- **RAM:** 710GB
- **Path:** `C:\Users\k1812261\claude_code\tt_project_malmo`

### What's Ready
| Component | Status |
|-----------|--------|
| Python 3.11.9 | Installed |
| Virtual env (`venv_win`) | Created with all deps |
| PyTorch 2.5.1+cu121 | Working (GPU verified) |
| Server dependencies | All installed |
| Ollama adapter | Added for easy local LLM |
| Batch scripts | Created for easy startup |
| Minecraft/Malmo | Working on ports 9000-9002 |

### Quick Commands
```powershell
cd C:\Users\k1812261\claude_code\tt_project_malmo\tt_project_malmo\tt_malmo_mcp_server

# Start MCP Server
./venv_win/Scripts/python.exe -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8080

# Start Dashboard (optional)
./venv_win/Scripts/python.exe -m streamlit run dashboard.py

# Launch benchmark
./venv_win/Scripts/python.exe run_city_benchmark.py --speed 2x --agents 3 --no-spectator --time-limit 60
```

### Launching Minecraft Instances
Each agent needs its own Minecraft instance. Edit `run/config/malmomodCLIENT.cfg` for each port:
```bash
cd tt_project_malmo\malmo\Minecraft

# Edit config: I:portOverride=9000 (or 9001, 9002)
# Then launch:
./gradlew runClient
```

---

## City Building Benchmark - Session Report (2026-02-05)

### What Was Tested
3 PIANO agents (Alice, Bob, Charlie) running at 2x speed, building a city collaboratively for ~60 hours.

### Fixes Applied During Session

| Issue | Root Cause | Fix Applied | File |
|-------|------------|-------------|------|
| Agents stuck at (0,0,4,0) | `_process_observation()` ignored MalmoEnv info JSON | Parse info string for real position/inventory | `environment_manager.py` |
| Agents not moving | Single-tick commands insufficient | Execute 10 ticks per movement command | `environment_manager.py` |
| Turn oscillation | `turn ±1` for 10 ticks overshoots at 180°/sec | Proportional turning based on yaw error | `environment_manager.py` |
| Agents walk away forever | No boundary enforcement | Nav override at 50-block radius | `environment_manager.py` |
| Agents stuck in holes | No underground detection | Jump when y < 3 | `environment_manager.py` |
| Empty observations | MalmoEnv returns empty info transiently | Last-known-good observation cache | `environment_manager.py` |
| Mining through ground | `attack 1` while looking down | Reset pitch before/after every action | `environment_manager.py` |
| Void death | Agents mined through bedrock | Barrier floor at y=0 in mission XML | `mission_builder.py` |
| Can't die anyway | Survival mode allows damage | Changed to Creative mode | `mission_builder.py` |
| Inventory not visible | Missing observation handler | Added `ObservationFromFullInventory` | `mission_builder.py` |
| Empty map | Sparse resources | Generated 400+ resource blocks | `mission_builder.py` |

### Current State
- All three agents run stably for thousands of steps
- Navigation override keeps agents in building area
- Stuck detection + recovery works
- Death detection implemented but **respawn fails mid-mission**

### CRITICAL TODO: Fix Agent Respawn

**Problem:** When an agent dies, `reset()` is called but fails because MalmoEnv's reset tries to start a new mission. During an active multi-agent mission, this doesn't work.

**Attempted:** `env.reset()` mid-mission → fails with connection error

**Options to Fix:**

1. **Adventure Mode** (RECOMMENDED):
   - Change `mode="Creative"` to `mode="Adventure"` in mission XML
   - Adventure mode: Can use/place blocks but cannot break them
   - Prevents mining through ground entirely
   - File: `mission_builder.py` line ~230

2. **MalmoEnv Reconnection:**
   - Create new `malmoenv.make()` instance
   - Call `init()` with same mission XML, same role
   - Should rejoin existing mission
   - Untested, may need Malmo source changes

3. **Gamerules in Mission XML:**
   - Add `<gamerules><rule name="keepInventory">true</rule></gamerules>`
   - Add `<rule name="naturalRegeneration">true</rule>`
   - Not sure if Malmo supports these in XML

### Key Files Modified

**`malmo_integration/environment_manager.py`** - Main control loop:
- `step()` - Added last-good-obs cache, done coercion
- `_process_observation()` - Flags `_info_empty`, parses inventory
- `_run_agent_loop_blocking()` - Death detection, stuck detection, nav override, pitch reset
- `_execute_return_step()` - Proportional turning for nav return
- `_is_underground()`, `_needs_return_to_center()` - Helper checks

**`malmo_integration/mission_builder.py`** - Mission generation:
- Creative mode for agents
- Barrier floor generator string
- Rich resource generation (400+ blocks)
- ObservationFromFullInventory enabled

**`run_city_benchmark.py`** - Launcher:
- `--time-limit` flag (default 60 hours)
- Non-interactive mode (handles EOFError)

### Monitoring the Benchmark

```bash
# Check agent activity
curl http://localhost:8080/agents

# Check mission status
curl http://localhost:8080/mission/status

# View dashboard
http://localhost:8501

# Tail MCP server logs (find task ID from background process)
tail -f /path/to/task/output
```

### Stopping the Benchmark

```bash
curl -X POST http://localhost:8080/mission/stop
```

---

## Resources

- **Microsoft Malmo:** https://github.com/microsoft/malmo
- **MalmoEnv:** Gym-compatible Malmo wrapper
- **Ollama:** https://ollama.ai
- **Qwen 2.5 Coder 32B:** Local LLM via Ollama

---

## Contact

**Primary:** ricardo.twumasi@kcl.ac.uk
**GitHub Issues:** https://github.com/ricardotwumasi/tt_malmo/issues
