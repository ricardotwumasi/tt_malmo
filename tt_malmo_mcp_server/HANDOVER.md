# Malmo MCP Server - Developer Handover Document

**Date:** December 2025
**Project:** Multi-Agent Benchmarking System with PIANO Architecture
**Repository:** https://github.kcl.ac.uk/k1812261/tt_malmo
**Contact:** ricardo.twumasi@kcl.ac.uk

---

## Executive Summary

This project implements a multi-agent benchmarking system using Microsoft Project Malmo (Minecraft) as the evaluation environment. The system uses the PIANO (Parallel Information Aggregation via Neural Orchestration) cognitive architecture and Model Context Protocol (MCP) to coordinate multiple AI agents. Currently deployed locally and tested with Gemini 2.5 Flash; ready for CREATE Cloud deployment and expanded testing.

---

## Current Status

### ✅ Completed

1. **Core Infrastructure**
   - MCP server (FastAPI) with agent management API
   - PIANO cognitive architecture (5 modules)
   - LLM adapters (Gemini 2.5 Flash, Claude Opus 4.5 ready)
   - Malmo environment integration
   - Docker containerization
   - Comprehensive documentation

2. **Testing & Validation**
   - Local testing successful with Gemini 2.5 Flash
   - Agent connection verified
   - PIANO modules operational
   - Decision-making loop functional

3. **Repository & Documentation**
   - Code pushed to KCL GitHub
   - README.md, DEPLOY.md, MACOS_SETUP.md complete
   - Docker configurations ready

### 🚧 Pending Tasks

1. **Deploy to CREATE Cloud infrastructure**
2. **Test with 5-10 agents and validate MVP**
3. **Implement benchmarking system (metrics store, role analysis)**

---

## Project Architecture

```
┌─────────────────────────────────────────────┐
│         MCP Server (FastAPI)                │
│  - Agent Management API                     │
│  - WebSocket Support                        │
│  - Metrics Collection                       │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼─────────────┐ ┌────▼──────────────┐
│ PIANO Agent 1   │ │ PIANO Agent N     │
│ - Gemini/Claude │ │ - Gemini/Claude   │
│ - 5 Modules     │ │ - 5 Modules       │
└───┬─────────────┘ └────┬──────────────┘
    │                     │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │ Environment Manager │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │ Malmo/Minecraft     │
    │ (Headless Servers)  │
    └─────────────────────┘
```

### Key Components

**1. MCP Server** (`mcp_server/`)
- **server.py**: FastAPI application, endpoints for agent CRUD
- **agent_manager.py**: Agent lifecycle management
- **protocol/**: Message definitions

**2. PIANO Architecture** (`piano_architecture/`)
- **cognitive_controller.py**: Decision bottleneck, module aggregation
- **agent_state.py**: Thread-safe state management
- **modules/**: 5 cognitive modules (Perception, Action, Social, Goal, Memory)

**3. LLM Adapters** (`llm_adapters/`)
- **base_adapter.py**: Abstract interface
- **gemini_adapter.py**: Google Gemini integration (tested ✅)
- **claude_adapter.py**: Anthropic Claude (ready, not tested)

**4. Malmo Integration** (`malmo_integration/`)
- **environment_manager.py**: Bridges agents to Minecraft
- **mission_builder.py**: Mission XML generation

**5. Configuration** (`config.py`)
- Centralized env variables
- No hardcoded paths
- Deployment-agnostic

---

## Pending Tasks - Detailed Instructions

### Task 1: Deploy to CREATE Cloud Infrastructure

**Priority:** High
**Estimated Time:** 4-6 hours
**Dependencies:** CREATE Cloud account, VM access

#### Steps:

1. **Create VM on CREATE Cloud**
   ```
   - OS: Ubuntu 20.04 LTS
   - Flavor: m1.large (8GB RAM, 4 vCPUs)
   - Storage: 50GB
   - Security Groups: Allow ports 22, 8000, 9000-9010
   - Assign Floating IP
   ```

2. **SSH into VM and Install Docker**
   ```bash
   ssh ubuntu@<FLOATING_IP>
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Clone Repository**
   ```bash
   git clone https://github.kcl.ac.uk/k1812261/tt_malmo.git
   cd tt_malmo/tt_malmo_mcp_server
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env
   # Add: GOOGLE_API_KEY=<your_key>
   # Add: ANTHROPIC_API_KEY=<your_key> (if using Claude)
   ```

5. **Deploy with Docker Compose**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

6. **Verify Deployment**
   ```bash
   # Check services
   docker-compose ps

   # Check logs
   docker-compose logs -f mcp-server

   # Test health endpoint
   curl http://localhost:8000/health
   ```

7. **Test External Access**
   ```bash
   # From local machine:
   curl http://<FLOATING_IP>:8000/health
   ```

**Documentation:** See `DEPLOY.md` for complete guide

**Troubleshooting:**
- Port conflicts: Check `sudo lsof -i :<port>`
- Memory issues: Monitor with `docker stats`
- Connection issues: Verify security groups in CREATE dashboard

---

### Task 2: Test with 5-10 Agents and Validate MVP

**Priority:** High
**Estimated Time:** 8-12 hours
**Dependencies:** Task 1 completed

#### Steps:

1. **Create Test Agents**
   ```bash
   # Script to create 10 agents
   for i in {0..9}; do
     curl -X POST http://localhost:8000/agents \
       -H "Content-Type: application/json" \
       -d "{
         \"name\": \"Agent_Gemini_$i\",
         \"llm_provider\": \"gemini\",
         \"model\": \"gemini-2.5-flash\",
         \"role\": $i,
         \"traits\": [\"curious\", \"strategic\", \"collaborative\"]
       }"
     echo ""
   done
   ```

2. **Verify Agent Creation**
   ```bash
   curl http://localhost:8000/agents | python3 -m json.tool
   ```

3. **Start Agents in Mission**
   ```bash
   # For each agent, start decision loop
   AGENT_IDS=$(curl -s http://localhost:8000/agents | jq -r '.[].agent_id')
   for id in $AGENT_IDS; do
     curl -X POST http://localhost:8000/agents/$id/start
   done
   ```

4. **Monitor Agent Performance**
   ```bash
   # Watch logs
   docker-compose logs -f mcp-server

   # Check agent states
   for id in $AGENT_IDS; do
     curl http://localhost:8000/agents/$id/state
   done

   # Monitor metrics
   curl http://localhost:8000/metrics
   ```

5. **Run Multi-Agent Mission**
   - Use `mobchase_two_agents.xml` or custom multi-agent mission
   - Launch agents using `launch_agent_in_minecraft.py`
   - Monitor for 1000+ steps (or mission completion)

6. **Validation Criteria**
   - ✅ All agents connect successfully
   - ✅ PIANO modules generate decisions
   - ✅ Agents execute actions in Minecraft
   - ✅ No crashes or timeouts for 30+ minutes
   - ✅ Metrics collection works
   - ✅ Multi-agent coordination observable

**Key Files:**
- `launch_agent_in_minecraft.py`: Agent launcher
- `missions/`: Available mission XMLs
- `logs/`: Check for errors

---

### Task 3: Implement Benchmarking System

**Priority:** Medium
**Estimated Time:** 16-24 hours
**Dependencies:** Task 2 completed

#### Components to Implement:

**A. Metrics Store**

Create `benchmarking/metrics_store.py`:

```python
"""
Persistent storage for agent metrics.
Store in PostgreSQL or SQLite.
"""

class MetricsStore:
    def __init__(self, db_url):
        # Connect to database
        pass

    def record_decision(self, agent_id, timestamp, decision, reward):
        """Record each agent decision with outcome"""
        pass

    def record_episode(self, agent_id, episode_data):
        """Record complete episode metrics"""
        pass

    def get_agent_summary(self, agent_id):
        """Get aggregate metrics for agent"""
        return {
            'total_decisions': int,
            'avg_reward': float,
            'alignment_score': float,
            'autonomy_score': float,
            'episode_count': int
        }
```

**B. Role Analysis**

Create `benchmarking/role_analyzer.py`:

```python
"""
Analyze agent performance by role.
Roles: miner, scout, blacksmith, etc.
"""

class RoleAnalyzer:
    def analyze_role_performance(self, agent_id, role):
        """
        Measure role-specific metrics:
        - Miner: resources gathered
        - Scout: area explored
        - Builder: structures created
        """
        pass

    def compare_roles(self):
        """Compare performance across roles"""
        pass
```

**C. Alignment Scoring**

Create `benchmarking/alignment_scorer.py`:

```python
"""
Score agent alignment based on MACHIAVELLI framework.
"""

class AlignmentScorer:
    def score_decision(self, decision, context):
        """
        Score individual decision:
        - power_seeking: bool
        - harm_caused: float
        - deception: bool
        - ethical_violation: bool
        """
        pass

    def aggregate_alignment_score(self, agent_id):
        """Calculate overall alignment score"""
        pass
```

**D. Dashboard/Visualization**

Create `benchmarking/dashboard.py`:

```python
"""
Streamlit or Plotly dashboard for real-time metrics.
"""

import streamlit as st

def render_dashboard():
    st.title("Malmo Agent Benchmarking")

    # Agent comparison
    st.header("Agent Performance")
    # Plot: reward over time, decisions per minute, etc.

    # Alignment metrics
    st.header("Alignment Scores")
    # Heatmap of alignment violations

    # Role analysis
    st.header("Role Performance")
    # Bar chart comparing roles
```

#### Database Schema

```sql
CREATE TABLE agents (
    agent_id UUID PRIMARY KEY,
    name VARCHAR(255),
    llm_provider VARCHAR(50),
    role INT,
    created_at TIMESTAMP
);

CREATE TABLE decisions (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES agents(agent_id),
    timestamp TIMESTAMP,
    action VARCHAR(255),
    reasoning TEXT,
    reward FLOAT,
    alignment_score FLOAT
);

CREATE TABLE episodes (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES agents(agent_id),
    mission_name VARCHAR(255),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_reward FLOAT,
    steps INT,
    completed BOOLEAN
);

CREATE TABLE alignment_events (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES agents(agent_id),
    decision_id INT REFERENCES decisions(id),
    event_type VARCHAR(50), -- 'power_seeking', 'harm', 'deception'
    severity FLOAT,
    description TEXT
);
```

#### Integration Points

1. **Modify `cognitive_controller.py`:**
   ```python
   # Add after decision is made:
   from benchmarking.metrics_store import MetricsStore

   metrics = MetricsStore(config.DATABASE_URL)
   metrics.record_decision(agent_id, timestamp, decision, reward)
   ```

2. **Add endpoint to `server.py`:**
   ```python
   @app.get("/benchmarks/{agent_id}")
   async def get_benchmarks(agent_id: str):
       analyzer = RoleAnalyzer()
       scorer = AlignmentScorer()

       return {
           "performance": analyzer.analyze_role_performance(agent_id),
           "alignment": scorer.aggregate_alignment_score(agent_id),
           "metrics": metrics_store.get_agent_summary(agent_id)
       }
   ```

---

## Development Environment Setup

### Local Development (macOS)

1. **Prerequisites**
   - Python 3.9+
   - Java 8 (for Malmo)
   - Docker Desktop

2. **Install MalmoEnv**
   ```bash
   cd malmo/Minecraft
   ./setup_malmoenv.sh
   ```

3. **Create Virtual Environment**
   ```bash
   cd tt_malmo_mcp_server
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure API Keys**
   ```bash
   cp .env.example .env
   nano .env  # Add your API keys
   ```

5. **Test Locally**
   ```bash
   # Terminal 1: Start Malmo
   cd malmo/Minecraft
   ./launchClient.sh -port 9000 -env

   # Terminal 2: Start MCP Server
   cd tt_malmo_mcp_server
   source venv/bin/activate
   python -m uvicorn mcp_server.server:app --reload

   # Terminal 3: Test
   curl http://localhost:8000/health
   python test_gemini.py
   ```

---

## Key Configuration Files

| File | Purpose |
|------|---------|
| `.env` | API keys, deployment settings (NOT in git) |
| `.env.example` | Template for .env |
| `config.py` | Centralized configuration |
| `docker-compose.yml` | Multi-container orchestration |
| `Dockerfile` | MCP server container |
| `Dockerfile.malmo` | Malmo server container |
| `requirements.txt` | Python dependencies |

---

## Testing

### Unit Tests (To Be Implemented)

```bash
pytest tests/
```

### Integration Tests

```bash
# Test agent creation
python tests/test_agent_creation.py

# Test PIANO modules
python tests/test_piano_modules.py

# Test Malmo connection
python tests/test_malmo_integration.py
```

---

## Known Issues & Limitations

1. **macOS Display Bug**
   - Minecraft crashes on macOS with window threading error
   - **Workaround:** Deploy on Linux (CREATE Cloud)

2. **Gemini API Rate Limits**
   - Free tier: 15 requests/minute
   - **Solution:** Add rate limiting in `gemini_adapter.py`

3. **Mission XML Complexity**
   - Custom missions require careful XML structure
   - **Solution:** Use `mission_builder.py` or pre-built missions

4. **Memory Leaks (Potential)**
   - Long-running agents may accumulate memory
   - **Monitoring:** Use `docker stats` and log rotation

---

## Resources

### Documentation
- **README.md**: Project overview
- **DEPLOY.md**: Complete deployment guide
- **MACOS_SETUP.md**: Local development setup

### External Links
- [Malmo Documentation](https://github.com/microsoft/malmo)
- [CREATE Cloud Docs](https://docs.er.kcl.ac.uk/CREATE/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Gemini API](https://ai.google.dev/docs)

### Research Papers
- PIANO Architecture: `project_sid.pdf`
- MACHIAVELLI Benchmark: https://arxiv.org/abs/2304.03279
- AgentBench: https://github.com/THUDM/AgentBench
- World Models: https://arxiv.org/abs/1803.10122

---

## Contact & Support

**Primary Contact:** ricardo.twumasi@kcl.ac.uk
**CREATE Support:** support@er.kcl.ac.uk
**Repository Issues:** https://github.kcl.ac.uk/k1812261/tt_malmo/issues

---

## Quick Reference Commands

```bash
# Deployment
docker-compose up -d                    # Start all services
docker-compose down                     # Stop all services
docker-compose logs -f mcp-server       # View logs
docker-compose ps                       # Check status

# Agent Management
curl http://localhost:8000/agents       # List agents
curl -X POST http://localhost:8000/agents -d '{"name":"test",...}'  # Create
curl http://localhost:8000/agents/{id}/start  # Start agent

# Debugging
docker exec -it malmo-mcp-server bash   # Shell into container
docker-compose restart mcp-server       # Restart service
git log --oneline -10                   # Recent commits
```

---

## Success Criteria for Handover

- [ ] Successfully deploy to CREATE Cloud VM
- [ ] Run 5+ agents concurrently for 1+ hour
- [ ] Implement basic metrics storage
- [ ] Generate alignment scores for test agents
- [ ] Create performance comparison dashboard
- [ ] Document any new issues in GitHub
- [ ] Update README with findings

---

**Last Updated:** 2025-12-04
**Version:** 1.0
**Next Review:** After Task 2 completion

Good luck! The foundation is solid—time to scale and measure. 🚀
