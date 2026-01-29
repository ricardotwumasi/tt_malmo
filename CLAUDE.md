# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository is a planning workspace for developing a proof-of-concept AI "World Model" benchmarking test based on Microsoft's Project Malmo. The goal is to create a Minecraft-based evaluation platform for testing agentic AI performance across multiple domains.

### Evaluation Domains (in decreasing priority)
1. **Alignment**: How well agents align with human goals broadly, and organizational goals specifically
2. **Autonomy Score**: Degree of independent agent operation
3. **Beauty**: Aesthetic quality of agent outputs/creations
4. **Environmental Impact**: Energy consumption and human intervention required
5. **Economic Utility**: Practical economic value generated

### Planned Implementation Path
- Fork Microsoft Malmo from: https://github.com/microsoft/malmo
- Target hosting location: https://github.kcl.ac.uk/k1812261/tt_malmo
- Alternative: https://github.com/ricardotwumasi (then fork to github.kcl.ac.uk)
- Final deployment on CREATE: https://docs.er.kcl.ac.uk/

## Repository Structure

### Current Files
- `repo_summary.md`: Project concept and objectives document
- `microsoft-malmo-8a5edab282632443.txt`: Complete directory structure and README content from Microsoft Malmo repository
- `LaTeX/`: Academic papers and reference materials
  - `AIMag26-04-HLAI.pdf`: AI Magazine article on HLAI
  - `Dario Amodei — Machines of Loving Grace.pdf`: Reference document
  - `turing 1950.pdf`: Historical reference (Turing's Computing Machinery and Intelligence)
  - Peer-reviewed search results

## Microsoft Malmo Architecture (Reference)

The microsoft-malmo-8a5edab282632443.txt file contains the complete structure of the Malmo platform. Key architectural components:

### Core Components
- **AgentHost**: Main interface for running agents (C++, Python, Java, C# wrappers available)
- **MissionSpec**: XML-based mission definition system
- **WorldState**: Current state of the Minecraft world
- **Client-Server Architecture**: TCP-based communication between agents and Minecraft

### Language Support
- **Python**: Primary interface via MalmoEnv (gym-like environment) or native MalmoPython module
- **C++**: Native implementation with full API access
- **Java**: SWIG wrapper for Java integration
- **C#**: .NET wrapper via MalmoNET

### Mission System
- Missions defined via XML specifications
- Reward systems (timestamped rewards, chat rewards, item rewards, etc.)
- Multi-agent coordination support
- Video frame capture and observation APIs

### Key Directories in Malmo
- `Malmo/samples/Python_examples/`: ~40 Python example missions demonstrating various features
- `Malmo/src/`: Core C++ implementation (AgentHost, MissionSpec, network communication)
- `MalmoEnv/`: OpenAI Gym-compatible Python environment (preferred for new development)
- `Minecraft/`: Modified Minecraft client with Malmo mod

## Development Workflow

### Working with Malmo Reference
When examining Malmo architecture:
```bash
# Search the structure file for specific components
grep -i "pattern" microsoft-malmo-8a5edab282632443.txt

# Find file locations
grep "filename" microsoft-malmo-8a5edab282632443.txt

# Examine Python examples
grep -A 10 "Python_examples" microsoft-malmo-8a5edab282632443.txt
```

### Malmo Quick Start (from reference documentation)
The microsoft-malmo file shows three approaches to using Malmo:

1. **MalmoEnv** (Recommended for new projects)
   - Pure Python, no native compilation
   - OpenAI Gym-compatible API
   - Single port, simpler multi-agent protocol
   - Better for virtualization/containerization

2. **Native Python Wheel**
   ```bash
   pip3 install malmo
   ```

3. **Pre-built Binaries**
   - Launch Minecraft: `cd Minecraft && ./launchClient.sh [-port 10001]`
   - Run Python agent: `cd Python_Examples && python3 run_mission.py`
   - Default port range: 10000-11000

## Project Planning Notes

This is currently a **planning and research phase** repository. The actual Malmo fork and benchmark implementation have not yet been created.

### Next Steps (Future Development)
1. Fork the Malmo repository to target location
2. Design benchmark scenarios for each evaluation domain
3. Implement scoring/evaluation framework
4. Create custom missions for alignment, autonomy, and other metrics
5. Set up infrastructure on CREATE platform

### Academic Context
The LaTeX folder contains foundational papers that inform the theoretical approach to AI evaluation. When developing benchmarks, consider the historical and contemporary perspectives on AI capabilities and alignment from these references.
