# Malmo MCP Server with PIANO Architecture

Multi-agent benchmarking system using Project Malmo, Model Context Protocol (MCP), and PIANO (Parallel Information Aggregation via Neural Orchestration) architecture.

## Overview

This system enables multiple LLM agents (Claude Opus 4.5, Gemini 2.5 Flash) to interact with Minecraft through Project Malmo, using the PIANO architecture for cognitive processing. Designed for deployment on King's College London CREATE Cloud infrastructure.

## Architecture Components

1. **MCP Server** - FastAPI server coordinating multiple agents
2. **PIANO Architecture** - Cognitive processing with 5 concurrent modules
3. **Malmo Integration** - Environment manager bridging agents to Minecraft
4. **LLM Adapters** - Support for multiple LLMs (Gemini, Claude)

## Quick Start

### CREATE Cloud Deployment

1. Create Ubuntu 20.04 VM on CREATE Cloud (8GB RAM, 4 vCPUs)
2. Install Docker and Docker Compose
3. Clone repository and configure .env with API keys
4. Run: `docker-compose up -d`
5. Access at: `http://your-vm-ip:8000`

### Local Development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000
```

## Documentation

- Full deployment guide in DEPLOY.md
- API documentation: http://localhost:8000/docs
- CREATE Cloud docs: https://docs.er.kcl.ac.uk/CREATE/

## Contact

- GitHub: https://github.com/ricardotwumasi/tt_malmo
- CREATE Support: support@er.kcl.ac.uk
