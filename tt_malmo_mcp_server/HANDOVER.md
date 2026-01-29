# Malmo MCP Server - Developer Handover Document

**Date:** January 2025
**Project:** Multi-Agent AI Benchmarking System with PIANO Architecture
**Repository:** https://github.com/ricardotwumasi/tt_malmo
**Contact:** ricardo.twumasi@kcl.ac.uk

---

## Executive Summary

This project implements a multi-agent AI benchmarking system using Microsoft Project Malmo (Minecraft) as the evaluation environment. The system uses the PIANO (Parallel Information Aggregation via Neural Orchestration) cognitive architecture to coordinate multiple AI agents powered by various LLM providers (Gemini, OpenRouter, Cerebras, Cloudflare).

**Current Status:** MVP 80% complete - ready for deployment and testing.

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

### Priority 1: Deploy and Test on Linux Server

**Goal:** Get the full benchmark running on CREATE Cloud or another Linux server.

**Steps:**
1. Request CREATE Cloud VM (Ubuntu 22.04, 8GB RAM)
2. Clone repository with submodules
3. Run `./deploy.sh` for Docker deployment
4. Test with 5-10 agents

**Documentation:** See `LINUX_DEPLOYMENT.md`

### Priority 2: Complete Minecraft Integration Testing

**Goal:** Verify agents can control Minecraft via MalmoEnv.

**Current Issue:** macOS has LWJGL threading compatibility issues. Docker on Linux works.

**Steps:**
1. Deploy on Linux (Docker)
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
- [ ] Set up local development environment
- [ ] Run test suite (all tests pass)
- [ ] Start MCP server locally
- [ ] Create and list agents via API
- [ ] Understand PIANO architecture
- [ ] Review pending tasks above
- [ ] Access to API keys (Gemini recommended)

---

**Last Updated:** 2025-01-29
**Version:** 2.0
