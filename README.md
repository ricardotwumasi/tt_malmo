# Malmo AI Benchmark Platform

A platform for benchmarking AI agents in Minecraft using Microsoft's Project Malmo and the PIANO cognitive architecture.

## Overview

This project extends Microsoft's Project Malmo to create a standardized benchmarking environment for evaluating AI agent performance across multiple domains:

- **Alignment** - How well agents align with human/organizational goals
- **Autonomy** - Degree of independent operation
- **Performance** - Task completion, resource gathering, survival
- **Social Intelligence** - Multi-agent cooperation and communication
- **Economic Utility** - Practical value generation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (FastAPI)                      │
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
│  │              │    (Bottleneck)      │   (Gemini/    │   │
│  │              └─────────────────────┘    Claude/etc) │   │
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

## Features

### Multi-Provider LLM Support
- **Google Gemini** (gemini-2.5-flash-lite) - Free tier available
- **OpenRouter** - Access to DeepSeek, GLM, Llama models
- **Cerebras** - Ultra-fast inference (1M tokens/day free)
- **Cloudflare Workers AI** - Reliable infrastructure
- **Anthropic Claude** - Premium option

### PIANO Cognitive Architecture
Based on Altera's Project Sid research:
- 5 concurrent processing modules
- Information bottleneck for decision-making
- Multi-timescale memory systems
- Action awareness for hallucination prevention

### Benchmarking Framework
- PostgreSQL-backed metrics storage
- Domain-specific scoring (Alignment, Autonomy, Performance, Social, Economic)
- Multi-agent performance tracking
- Human oversight dashboard

## Quick Start

### Prerequisites
- Python 3.10+
- Docker Desktop (for Malmo/Minecraft)
- At least one API key (Gemini recommended - free tier)

### Installation

```bash
# Clone the repository
git clone https://github.com/ricardotwumasi/tt_malmo.git
cd tt_malmo/tt_malmo_mcp_server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys
```

### Run the MCP Server

```bash
# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start the server
python -m uvicorn mcp_server.server:app --reload --host 0.0.0.0 --port 8000
```

### Create and Run AI Agents

```bash
# Create an agent
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{"name":"Explorer","llm_type":"gemini","role":0,"traits":["curious"]}'

# Start the agent
curl -X POST http://localhost:8000/agents/AGENT_ID/start

# View API docs
open http://localhost:8000/docs
```

## Docker Deployment

For full Minecraft integration, use Docker:

```bash
cd tt_malmo_mcp_server

# Start Malmo in Docker
./start_docker_malmo.sh

# Or start full stack
./start_docker_malmo.sh --full
```

See [DOCKER_SETUP.md](tt_malmo_mcp_server/DOCKER_SETUP.md) for detailed instructions.

## Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART_APPLE_SILICON.md](tt_malmo_mcp_server/QUICKSTART_APPLE_SILICON.md) | Setup guide for M1/M2/M3 Macs |
| [DOCKER_SETUP.md](tt_malmo_mcp_server/DOCKER_SETUP.md) | Docker deployment guide |
| [LINUX_DEPLOYMENT.md](tt_malmo_mcp_server/LINUX_DEPLOYMENT.md) | Linux server deployment (Ubuntu/Debian) |
| [MACOS_SETUP.md](tt_malmo_mcp_server/MACOS_SETUP.md) | macOS setup instructions |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Current development status |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Project Structure

```
tt_malmo/
├── tt_malmo_mcp_server/          # Main application
│   ├── mcp_server/               # FastAPI server
│   ├── piano_architecture/       # PIANO cognitive modules
│   ├── llm_adapters/             # LLM provider integrations
│   ├── malmo_integration/        # Malmo/Minecraft bridge
│   ├── benchmarking/             # Metrics and evaluation
│   ├── deployment/               # Docker configurations
│   └── tests/                    # Test suite (95+ tests)
├── malmo/                        # Microsoft Malmo (submodule)
├── CHANGELOG.md                  # Version history
├── PROJECT_STATUS.md             # Development status
└── README.md                     # This file
```

## Testing

```bash
cd tt_malmo_mcp_server
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=term-missing
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server health check |
| `/agents` | GET | List all agents |
| `/agents` | POST | Create new agent |
| `/agents/{id}` | GET | Get agent details |
| `/agents/{id}` | DELETE | Delete agent |
| `/agents/{id}/start` | POST | Start agent PIANO loop |
| `/agents/{id}/stop` | POST | Stop agent |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.txt) file for details.

## Acknowledgments

- [Microsoft Project Malmo](https://github.com/microsoft/malmo) - Minecraft AI platform
- [Altera Project Sid](https://altera.al/) - PIANO architecture research
- [Google Gemini](https://ai.google.dev/) - LLM provider

## Contact

Ricardo Twumasi - [@ricardotwumasi](https://github.com/ricardotwumasi)

Project Link: [https://github.com/ricardotwumasi/tt_malmo](https://github.com/ricardotwumasi/tt_malmo)
