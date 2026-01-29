# Changelog

All notable changes to the Malmo AI Benchmark project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.0] - 2025-01-29

### Added
- **Multi-Provider LLM Support**: Added adapters for OpenRouter, Cerebras, and Cloudflare Workers AI
- **LLM Adapter Factory**: New factory pattern for easy adapter instantiation (`llm_adapters/factory.py`)
- **Docker Support**: Complete Docker configuration for running Malmo on Linux
  - `Dockerfile.malmo` - Linux container for Minecraft with Malmo mod
  - `Dockerfile.mcp_server` - Container for MCP server
  - `docker-compose.yml` - Full stack orchestration
  - `docker-compose.malmo-only.yml` - Malmo-only for local development
- **Benchmarking Framework**:
  - `benchmarking/metrics_store.py` - PostgreSQL/in-memory metrics storage
  - `benchmarking/evaluator.py` - BenchmarkEvaluator with domain scoring
- **Comprehensive Test Suite**: 95+ tests covering all major components
  - Unit tests for LLM adapters, PIANO modules, mission builder
  - Integration tests for MCP server and environment manager
- **Documentation**:
  - `QUICKSTART_APPLE_SILICON.md` - Complete Apple Silicon setup guide
  - `DOCKER_SETUP.md` - Docker configuration guide
  - `LINUX_DEPLOYMENT.md` - Linux server deployment guide with systemd and nginx
  - `CHANGELOG.md` - This changelog
- **Helper Scripts**:
  - `start_docker_malmo.sh` - Easy Docker management
  - `launch_malmo.sh` - Native Malmo launcher
  - `deploy.sh` - Automated deployment for Docker and local setups
  - `monitor_agents.py` - Human oversight dashboard
  - `test_malmo_integration.py` - End-to-end integration test
  - `test_malmo_simple.py` - Simple connection test
  - `setup_malmo_apple_silicon.sh` - Automated Apple Silicon setup

### Changed
- **Gemini Model**: Updated default from `gemini-2.5-flash` to `gemini-2.5-flash-lite` (free tier)
- **Docker Configuration**: Added `platform: linux/amd64` for ARM compatibility
- **Agent Manager**: Now uses factory pattern for LLM adapter creation
- **Mission Builder**: Added `VideoProducer` element to simple test missions for MalmoEnv compatibility
- **Environment Manager**: Added `StringActionSpace` support for string-based Malmo commands

### Fixed
- ARM architecture compatibility in Docker containers
- MalmoEnv VideoProducer assertion error
- Test suite XML namespace handling

### Known Issues
- Native Malmo on macOS Apple Silicon crashes due to LWJGL threading issues
- Workaround: Use Docker for Malmo/Minecraft

## [0.1.0] - 2024-11-26

### Added
- Initial PIANO Architecture implementation
  - Cognitive Controller (bottleneck)
  - 5 concurrent modules: Perception, Social Awareness, Goal Generation, Action Awareness, Memory Consolidation
- MCP Server with FastAPI
  - REST API for agent management
  - WebSocket support for real-time updates
- LLM Adapters
  - Gemini adapter (Google AI)
  - Claude adapter (Anthropic)
- Malmo Integration
  - Mission Builder for XML generation
  - Environment Manager (partial)
- Project documentation
  - README.md
  - MACOS_SETUP.md
  - DEPLOY.md

---

## Version History

| Version | Date | Summary |
|---------|------|---------|
| 0.2.0 | 2025-01-29 | Multi-LLM support, Docker, benchmarking, test suite |
| 0.1.0 | 2024-11-26 | Initial PIANO architecture and MCP server |
