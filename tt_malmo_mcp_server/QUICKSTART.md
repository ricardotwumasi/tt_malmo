# Quick Start Guide

## What Has Been Built

The MVP implementation of the Malmo MCP Server is now complete with:

### Core Components ✅
1. **PIANO Architecture** (piano_architecture/)
   - Agent State with thread-safe operations
   - Cognitive Controller with bottleneck architecture
   - Action Awareness module (prevents hallucinations)
   - Perception, Social Awareness, Goal Generation, Memory Consolidation modules

2. **MCP Server** (mcp_server/)
   - FastAPI REST API for agent management
   - WebSocket support for real-time communication
   - Agent Manager for lifecycle orchestration

3. **LLM Adapters** (llm_adapters/)
   - Claude Opus 4.5 adapter (Anthropic API)
   - Gemini 3.0 Pro adapter (Google AI API)

4. **Malmo Integration** (malmo_integration/)
   - Mission Builder for multi-agent XML generation
   - Support for 5-50 agent scenarios

5. **Deployment** (deployment/)
   - Docker Compose configuration
   - Dockerfiles for MCP server and Malmo
   - PostgreSQL for metrics storage

## Next Steps (To Run the MVP)

### Step 1: Fork Malmo Repository ⚠️ MANUAL STEP

```bash
# Option 1: Fork to KCL GitHub (preferred)
# Go to: https://github.com/microsoft/malmo
# Click "Fork" and create fork at: https://github.kcl.ac.uk/k1812261/tt_malmo

# Option 2: Fork to personal GitHub (backup)
# Fork to: https://github.com/ricardotwumasi/tt_malmo

# Then clone the fork
cd /Users/k1812261/claude_code/tt_project_malmo
git clone https://github.kcl.ac.uk/k1812261/tt_malmo malmo
```

### Step 2: Get API Keys ⚠️ MANUAL STEP

```bash
# Anthropic API Key
# Visit: https://console.anthropic.com/
# Create API key for Claude Opus 4.5

# Google AI API Key
# Visit: https://makersuite.google.com/app/apikey
# Create API key for Gemini 3.0 Pro
```

### Step 3: Setup Environment

```bash
cd tt_malmo_mcp_server

# Copy and edit environment variables
cp .env.example .env
nano .env  # Add your API keys
```

### Step 4: Run Locally (Development)

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run MCP server (terminal 1)
python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000

# Test with curl (terminal 2)
curl http://localhost:8000/health
```

### Step 5: Run with Docker (Production)

```bash
cd deployment

# Start all services
docker-compose up --build

# Verify services are running
docker ps

# Check logs
docker-compose logs -f mcp_server
```

### Step 6: Create and Start Agents

```bash
# Create Claude agent
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Explorer_Claude",
    "llm_type": "claude",
    "role": 0,
    "traits": ["curious", "adventurous"]
  }'

# Save the agent_id from response
AGENT_ID="<agent_id_from_response>"

# Start agent's PIANO architecture
curl -X POST http://localhost:8000/agents/$AGENT_ID/start

# Check agent status
curl http://localhost:8000/agents/$AGENT_ID
```

## Testing the System

### Test 1: Create Multiple Agents (MVP: 5-10 agents)

```bash
# Create 5 agents with different LLMs and traits
for i in {1..3}; do
  curl -X POST http://localhost:8000/agents \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"Agent_Claude_$i\",\"llm_type\":\"claude\",\"role\":$i,\"traits\":[\"curious\",\"cooperative\"]}"
done

for i in {4..5}; do
  curl -X POST http://localhost:8000/agents \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"Agent_Gemini_$i\",\"llm_type\":\"gemini\",\"role\":$i,\"traits\":[\"analytical\",\"resourceful\"]}"
done

# List all agents
curl http://localhost:8000/agents | jq '.'
```

### Test 2: Monitor PIANO Architecture

```bash
# Watch server logs to see PIANO modules running
docker-compose logs -f mcp_server | grep -E "(perception|social_awareness|goal_generation|action_awareness|cognitive_controller)"

# You should see output like:
# [Agent_Claude_1] Decision: explore - Looking for resources in the area
# [Agent_Gemini_4] Goal Generated: Find wood to build shelter
# Action Awareness: Action 'move_forward' succeeded
```

### Test 3: Generate Malmo Mission

```bash
# Run mission builder to generate XML
cd malmo_integration
python3 mission_builder.py

# This generates mission XML for 10 agents
# Output will show mission structure with spawn points, resources, etc.
```

## Deploying to CREATE Cloud

### Step 1: Request CREATE Access ⚠️ MANUAL STEP

Email CREATE support:
```
To: support@er.kcl.ac.uk
Subject: CREATE Cloud Project Request - AI Agent Benchmarking

Dear CREATE Support,

I am requesting a CREATE Cloud project for AI agent benchmarking research using Microsoft Malmo.

Requirements:
- Ubuntu 22.04 VM
- Ports: 8000 (MCP server), 9000-9010 (Malmo), 5432 (PostgreSQL)
- Storage: ~50GB for Docker containers and logs
- Optional: A100 GPU reservation for 2-month experiment

Project: tt_malmo - Multi-agent AI benchmarking in Minecraft
Supervisor: [Your supervisor name]
Department: [Your department]

Thank you,
[Your name]
```

### Step 2: Deploy to CREATE VM

Once VM is provisioned:

```bash
# SSH to VM
ssh your_username@create_vm_ip

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git

# Clone repository
git clone https://github.kcl.ac.uk/k1812261/tt_malmo
cd tt_malmo/tt_malmo_mcp_server

# Setup environment
cp .env.example .env
nano .env  # Add API keys

# Start services
cd deployment
sudo docker-compose up -d

# Check status
sudo docker-compose ps
sudo docker-compose logs -f
```

### Step 3: Open Firewall Ports

Work with CREATE support to:
- Open port 8000 (MCP server)
- Open ports 9000-9010 (Malmo agents)
- Ensure Code of Connection compliance

## What's Still TODO for Full Implementation

### High Priority
1. **Benchmarking System** (benchmarking/)
   - PostgreSQL schema for metrics
   - Item progression tracker
   - Role analysis (using LLM to infer agent roles)
   - Social graph builder

2. **Malmo Environment Manager** (malmo_integration/)
   - Connection pooling to Malmo instances
   - Multi-agent coordination protocol
   - Observation/action translation

3. **Remaining PIANO Modules** (piano_architecture/modules/)
   - 5 additional modules from Project Sid
   - Full parallel execution
   - Inter-module communication

### Medium Priority
4. **Testing**
   - Unit tests for all modules
   - Integration tests for agent lifecycle
   - Load testing for 50 agents

5. **Monitoring**
   - Real-time dashboard
   - Prometheus metrics
   - Grafana visualization

### Low Priority
6. **Advanced Features**
   - Cultural transmission metrics
   - Long-term civilizational benchmarks
   - Multi-world experiments

## Current Limitations

1. **Malmo Integration**: Mission builder is complete, but environment manager needs full implementation to connect agents to live Malmo instances

2. **Benchmarking**: Metrics storage schema and analysis tools need implementation

3. **Scale Testing**: System designed for 5-10 agents (MVP) and 50 agents (target), but not yet tested at scale

4. **Module Count**: 5 core PIANO modules implemented, 5 additional modules needed for full architecture

## Success Criteria for MVP

- ✅ PIANO architecture implemented and functional
- ✅ MCP server running with REST + WebSocket
- ✅ Multiple LLM support (Claude + Gemini)
- ✅ Docker deployment configured
- ⚠️ Connect to Malmo and run 5-10 agents (requires Malmo fork + environment manager)
- ⚠️ Collect basic benchmarking metrics (requires benchmarking system)
- ⚠️ Deploy on CREATE Cloud (requires CREATE access)

## Getting Help

### Documentation
- Full documentation: `README.md`
- Implementation plan: `/Users/k1812261/.claude/plans/joyful-napping-dream.md`
- Codebase overview: `CLAUDE.md`

### Support
- GitHub Issues: https://github.kcl.ac.uk/k1812261/tt_malmo/issues
- CREATE Support: support@er.kcl.ac.uk (Mon-Fri, 10:00-16:00)

### Key Files to Review
1. `piano_architecture/agent_state.py` - Core data structure
2. `piano_architecture/cognitive_controller.py` - Decision-making bottleneck
3. `piano_architecture/modules/action_awareness.py` - Hallucination prevention
4. `mcp_server/server.py` - API endpoints
5. `mcp_server/agent_manager.py` - Agent orchestration
6. `malmo_integration/mission_builder.py` - Mission generation

---

**Status**: MVP Core Implementation Complete
**Ready for**: Local testing and CREATE deployment
**Blockers**: Malmo fork, API keys, CREATE access
