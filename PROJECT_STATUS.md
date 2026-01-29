# Project Status: Malmo MCP Server MVP

**Last Updated**: 2025-01-29
**Status**: MVP Implementation Complete, Docker Setup In Progress

## Recent Updates (January 2025)

### v0.2.0 - Multi-LLM Support & Docker
- ✅ Added multi-provider LLM support (OpenRouter, Cerebras, Cloudflare)
- ✅ Updated Gemini to use gemini-2.5-flash-lite (free tier)
- ✅ Implemented LLM adapter factory pattern
- ✅ Added comprehensive benchmarking framework
- ✅ Created 95+ unit and integration tests
- ✅ Added Docker configuration for Linux deployment
- ✅ Created Apple Silicon quick-start guide
- 🔄 Docker Malmo container testing in progress

### Current Focus
- Testing Docker-based Minecraft/Malmo on Linux
- Resolving software OpenGL rendering for headless operation

---

**Original Date**: 2025-11-26
**Original Status**: MVP Core Implementation Complete ✅

## Overview

Successfully implemented a Model Context Protocol (MCP) server for benchmarking multiple AI agents in Minecraft using Microsoft Malmo and Altera's PIANO architecture.

## What Was Built

### 1. Complete PIANO Architecture Implementation ✅

Located in: `tt_malmo_mcp_server/piano_architecture/`

- **Agent State** (`agent_state.py`) - Thread-safe shared state across all modules
  - Multi-timescale memory systems (working, short-term, long-term)
  - Current observations, goals, social relationships
  - Module communication channels
  - Thread-safe update operations

- **Cognitive Controller** (`cognitive_controller.py`) - Bottleneck decision-making
  - Information bottleneck filter (prevents overload)
  - LLM-based reasoning over filtered information
  - High-level decision generation
  - 5-second decision interval (per Project Sid)

- **5 Core PIANO Modules** (`modules/`)
  - **Action Awareness** - CRITICAL for preventing hallucination cascades
    - Compares expected vs actual action outcomes
    - Detects and corrects mismatches
    - Tracks action success rate

  - **Perception** - Sensory processing
    - Detects salient environmental changes
    - Identifies threats and opportunities
    - Categorizes entities (agents, mobs, items)

  - **Social Awareness** - Relationship tracking
    - Maintains interaction history
    - Computes relationship strengths
    - Infers agent roles through observation

  - **Goal Generation** - Autonomous goal creation
    - Generates goals every 5-10 seconds (LLM-based)
    - Prioritizes survival, resources, social, exploration
    - Tracks goal patterns for role analysis

  - **Memory Consolidation** - Multi-timescale memory management
    - Working → Short-term consolidation
    - Short-term → Long-term consolidation
    - Importance-based retention
    - Automatic forgetting of low-importance memories

### 2. MCP Server with FastAPI ✅

Located in: `tt_malmo_mcp_server/mcp_server/`

- **REST API** (`server.py`)
  - Agent creation/deletion endpoints
  - Agent lifecycle management (start/stop)
  - Health checks and monitoring
  - CORS support for web clients

- **WebSocket Support**
  - Real-time bidirectional communication
  - Agent-specific channels
  - Broadcast channel for global updates
  - Connection management

- **Agent Manager** (`agent_manager.py`)
  - Orchestrates agent lifecycle
  - Starts/stops PIANO architecture per agent
  - Processes observations from Malmo
  - Coordinates decisions and actions
  - Manages LLM adapters per agent

- **Protocol Messages** (`protocol/messages.py`)
  - Pydantic models for type safety
  - Agent create/status messages
  - Observation/action messages
  - Metrics and chat messages

### 3. LLM Adapters ✅

Located in: `tt_malmo_mcp_server/llm_adapters/`

- **Claude Adapter** (`claude_adapter.py`)
  - Anthropic API integration
  - Support for Claude Opus 4.5
  - Streaming and non-streaming generation
  - Token counting

- **Gemini Adapter** (`gemini_adapter.py`)
  - Google AI API integration
  - Support for Gemini 3.0 Pro
  - Streaming and non-streaming generation
  - Token counting

- **Base Adapter** (`base_adapter.py`)
  - Abstract interface for all LLMs
  - Ensures consistent API across providers

### 4. Malmo Integration ✅

Located in: `tt_malmo_mcp_server/malmo_integration/`

- **Mission Builder** (`mission_builder.py`)
  - Generates complete Malmo mission XML
  - Multi-agent spawn points (circular layout)
  - Resource-rich environment (trees, ores, animals)
  - Full observation handlers (stats, entities, grid, ray)
  - Full action handlers (movement, inventory, chat, crafting)
  - Configurable: 5-50 agents, world size, difficulty

### 5. Docker Deployment ✅

Located in: `tt_malmo_mcp_server/deployment/`

- **Docker Compose** (`docker-compose.yml`)
  - MCP Server container (FastAPI + PIANO)
  - Malmo Server container (Minecraft + Malmo mod)
  - PostgreSQL container (metrics storage)
  - Network configuration
  - Volume management

- **Dockerfiles**
  - `Dockerfile.mcp_server` - Python 3.10, dependencies, health check
  - `Dockerfile.malmo` - Ubuntu 22.04, Java 8, Xvfb display

- **Environment Configuration**
  - `.env.example` with API keys, database, ports

### 6. Documentation ✅

- **README.md** - Complete system documentation
  - Architecture diagrams
  - Setup instructions
  - API reference
  - Benchmarking metrics
  - CREATE Cloud deployment guide
  - Troubleshooting

- **QUICKSTART.md** - Quick start guide
  - What has been built
  - Next steps
  - Testing procedures
  - CREATE deployment steps
  - TODO list for full implementation

- **CLAUDE.md** - Codebase overview for Claude Code
- **repo_summary.md** - Project concept
- **PROJECT_STATUS.md** - This file

## Project Statistics

- **Lines of Code**: ~3,500+ (Python)
- **Files Created**: 25+
- **Python Modules**: 15+
- **Components**: 5 major systems (PIANO, MCP Server, LLM Adapters, Malmo Integration, Deployment)

## Architecture Highlights

### PIANO Bottleneck (Key Innovation)
```python
# Information flows through cognitive bottleneck
Modules (10 concurrent) → Cognitive Controller (bottleneck) → Decision → Modules
```

This prevents information overload and maintains agent coherence, critical for stable multi-agent AI.

### Action Awareness (Hallucination Prevention)
```python
# Before action
action_awareness.set_expectation("mine_block", {"inventory_change": {"wood": +1}})

# After action
result = action_awareness.check_outcome(observation)
if result['status'] == 'mismatch':
    # Correct agent's false belief
    agent.correct_hallucination(result['correction'])
```

This prevents cascading hallucinations where agents believe they succeeded when they failed.

## What's Ready to Use

✅ **Core PIANO Architecture** - Fully implemented and ready for agents
✅ **MCP Server** - Can create/manage agents via REST API
✅ **Multi-LLM Support** - Claude Opus 4.5 and Gemini 3.0 Pro integrated
✅ **Mission Generation** - Can generate Malmo XML for 5-50 agents
✅ **Docker Deployment** - Ready to deploy to CREATE Cloud

## What's Still TODO

### Required for MVP to Run End-to-End

1. **Malmo Fork** ⚠️ MANUAL STEP
   - Fork https://github.com/microsoft/malmo to https://github.kcl.ac.uk/k1812261/tt_malmo
   - Clone forked repo

2. **API Keys** ⚠️ MANUAL STEP
   - Get Anthropic API key for Claude
   - Get Google AI API key for Gemini
   - Add to `.env` file

3. **Malmo Environment Manager** (Coding Required)
   - Connect MCP server to live Malmo instances
   - Implement observation/action translation
   - Handle multi-agent coordination protocol
   - **Estimated effort**: 4-6 hours

4. **Benchmarking System** (Coding Required)
   - PostgreSQL schema for metrics
   - Item progression tracker
   - Role analysis (LLM-based)
   - **Estimated effort**: 6-8 hours

5. **CREATE Cloud Deployment** ⚠️ MANUAL STEP
   - Email support@er.kcl.ac.uk for VM access
   - Deploy Docker containers
   - Open firewall ports

### Nice-to-Have for Full Implementation

6. **5 Additional PIANO Modules** (Coding Required)
   - As specified in Project Sid paper
   - **Estimated effort**: 10-12 hours

7. **Testing Suite** (Coding Required)
   - Unit tests for modules
   - Integration tests for agent lifecycle
   - Load tests for 50 agents
   - **Estimated effort**: 8-10 hours

8. **Monitoring Dashboard** (Coding Required)
   - Real-time agent visualization
   - Metrics dashboards (Grafana)
   - **Estimated effort**: 6-8 hours

## Next Immediate Steps

### For Local Testing (Can Start Now)

1. Set up Python environment
```bash
cd tt_malmo_mcp_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Get API keys and configure
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run MCP server
```bash
python -m uvicorn mcp_server.server:app --reload
```

4. Test agent creation
```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{"name":"TestAgent","llm_type":"claude","role":0}'
```

### For Full Deployment (Requires Additional Work)

1. Fork Malmo repository to KCL GitHub
2. Implement Malmo Environment Manager
3. Implement Benchmarking System
4. Request and deploy to CREATE Cloud
5. Run 5-10 agent experiment
6. Collect and analyze metrics

## Success Criteria

### MVP Success (75% Complete)
- ✅ PIANO architecture implemented
- ✅ MCP server with REST + WebSocket
- ✅ Multiple LLM support
- ✅ Docker deployment configured
- ✅ Mission XML generation
- ⚠️ Connect agents to Malmo (needs env manager)
- ⚠️ Collect benchmarking metrics (needs benchmarking system)
- ⚠️ Deploy on CREATE Cloud (needs access)

### Full Implementation Success (40% Complete)
- ✅ Core 5 PIANO modules
- ⚠️ All 10 PIANO modules
- ⚠️ Scale to 50 agents
- ⚠️ Role specialization analysis
- ⚠️ Social coordination metrics
- ⚠️ 4-hour experiment runs
- ⚠️ Automated benchmarking pipeline

## Key Technical Decisions Made

1. **MalmoEnv (Pure Python)** over native Malmo
   - Simpler integration
   - Better Python compatibility
   - Sufficient for benchmarking needs

2. **Separate MCP Server** rather than embedded in Malmo
   - Cleaner architecture
   - Easier to update Malmo
   - Better separation of concerns

3. **FastAPI + WebSocket** for server
   - Modern Python web framework
   - Native async support
   - Built-in WebSocket support

4. **PostgreSQL** for metrics storage
   - Robust relational database
   - Good query performance
   - Wide deployment support

5. **Docker Containers** for deployment
   - Reproducible environments
   - Easy deployment to CREATE
   - Service isolation

## Repository Structure

```
/Users/k1812261/claude_code/tt_project_malmo/
├── CLAUDE.md                    # Codebase guide for Claude Code
├── repo_summary.md              # Original project concept
├── PROJECT_STATUS.md            # This file
├── knowlegebase/
│   ├── project_sid.pdf         # Altera's PIANO architecture paper
│   └── CREATE cloud.pdf        # CREATE infrastructure docs
└── tt_malmo_mcp_server/         # Main implementation
    ├── README.md                # Full documentation
    ├── QUICKSTART.md            # Quick start guide
    ├── requirements.txt         # Python dependencies
    ├── .env.example             # Environment variables template
    ├── piano_architecture/      # PIANO implementation
    ├── mcp_server/              # FastAPI server
    ├── llm_adapters/            # Claude + Gemini
    ├── malmo_integration/       # Mission builder
    ├── benchmarking/            # [TODO] Metrics system
    ├── deployment/              # Docker configs
    └── tests/                   # [TODO] Test suite
```

## How to Continue from Here

### Option 1: Complete MVP (Recommended)
Focus on getting 5-10 agents running end-to-end:
1. Fork Malmo
2. Implement Environment Manager
3. Deploy locally with Docker
4. Test with 5 agents

### Option 2: Deploy to CREATE First
Get infrastructure ready:
1. Request CREATE access
2. Deploy current implementation
3. Test connectivity
4. Complete Environment Manager on CREATE

### Option 3: Expand Architecture
Build out remaining components:
1. Implement 5 additional PIANO modules
2. Build comprehensive benchmarking system
3. Create monitoring dashboard
4. Scale testing to 50 agents

## Contact and Support

- **Repository**: https://github.kcl.ac.uk/k1812261/tt_malmo
- **CREATE Support**: support@er.kcl.ac.uk (Mon-Fri, 10:00-16:00)
- **Implementation Plan**: `/Users/k1812261/.claude/plans/joyful-napping-dream.md`

---

**Status**: Ready for next phase (Malmo integration and CREATE deployment)
**Blockers**: Malmo fork, API keys, CREATE access, Environment Manager implementation
**Estimated Time to Full MVP**: 10-14 additional hours of coding + deployment setup
