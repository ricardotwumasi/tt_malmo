# Windows Deployment Guide

Deploy the Malmo AI Benchmark platform on a Windows workstation with NVIDIA GPU for high-performance local LLM inference.

---

## Quick Start (After Automated Setup)

The automated setup has already configured most components. Here's what's ready:

### Already Installed
- Python 3.11.9
- Virtual environment (`venv_win`) with all dependencies
- PyTorch 2.5.1 with CUDA 12.1 (GPU: NVIDIA L40S detected)
- FastAPI, Uvicorn, Streamlit, and all server dependencies
- Ollama adapter (recommended for Windows local LLM)

### Run These Scripts
```powershell
cd C:\Users\k1812261\claude_code\tt_project_malmo\tt_project_malmo\tt_malmo_mcp_server

# Start MCP Server
.\start_server.bat

# Start Dashboard (separate terminal)
.\start_dashboard.bat
```

### For Local LLM (Recommended: Ollama)
1. Download Ollama: https://ollama.com/download/windows
2. Install (works without admin - installs to user directory)
3. Run these scripts:
```powershell
.\start_ollama.bat        # Start Ollama server
.\pull_ollama_models.bat  # Download models
```

### Remaining Manual Steps
1. **Java 8** (for Minecraft) - Run with UAC approval:
   ```powershell
   winget install EclipseAdoptium.Temurin.8.JDK
   ```

---

## Original Documentation Below

## Target System Specifications

| Component | Specification |
|-----------|---------------|
| **Device** | er-prj-393-vm02.kclad.ds.kcl.ac.uk |
| **OS** | Windows 10 64-bit |
| **CPU** | AMD EPYC-Milan @ 2.70 GHz |
| **RAM** | 710 GB |
| **GPU** | NVIDIA L40S (44 GB VRAM) |
| **Storage** | 200 GB (76 GB free) |
| **Platform** | OpenStack Nova VM |

## What You Can Run

With 44GB VRAM + 710GB RAM:

| Model | VRAM | Use Case |
|-------|------|----------|
| Qwen 2.5 Coder 32B | ~18.5GB | SOTA coding, beats GPT-4o |
| DeepSeek R1 Distill 70B | ~38-40GB | Best open logic/math reasoning |
| Mistral Small 24B | ~14.5GB | Exceptional creative writing |
| Llama 3.1 8B | ~5.5GB | Ultra-fast for simple tasks |
| DeepSeek R1 Full 671B | 710GB RAM | Hybrid mode (slow but max intelligence) |

---

## Phase 1: System Diagnostics

Run these commands in PowerShell to verify your system:

```powershell
# System info
systeminfo | findstr /B /C:"OS Name" /C:"Total Physical Memory"

# GPU verification
nvidia-smi

# CUDA version
nvcc --version

# Python version
python --version

# Git version
git --version

# Check available disk space
Get-PSDrive C | Select-Object Used, Free
```

### Expected Results

- `nvidia-smi` shows L40S with 44GB memory
- Python 3.10+ installed
- Git available
- Sufficient disk space (>50GB recommended)

---

## Phase 2: Environment Setup

### 2.1 Install Prerequisites (if not present)

```powershell
# Install Python 3.11 (if needed)
winget install Python.Python.3.11

# Install CUDA Toolkit 12.1+ (if not present)
# Download from: https://developer.nvidia.com/cuda-downloads

# Verify CUDA
nvcc --version
```

### 2.2 Clone Repository

```powershell
# Navigate to working directory
cd C:\Users\$env:USERNAME\Projects

# Clone with submodules
git clone --recurse-submodules https://github.com/ricardotwumasi/tt_malmo.git
cd tt_malmo
```

### 2.3 Create Python Virtual Environment

```powershell
# Create venv
cd tt_malmo_mcp_server
python -m venv venv

# Activate (PowerShell)
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip
```

### 2.4 Install Dependencies

```powershell
# Install base requirements
pip install -r requirements.txt

# Install GPU-specific packages (PyTorch with CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install vLLM
pip install vllm>=0.6.0
```

---

## Phase 3: Configure Environment

### 3.1 Create .env File

Copy the example and customize:

```powershell
Copy-Item .env.example .env
notepad .env
```

Add your API keys (optional for cloud providers):

```bash
# Required for cloud providers (if using)
OPENROUTER_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Local vLLM configuration (defaults work out of box)
VLLM_CODER_URL=http://localhost:8000/v1
VLLM_CODER_MODEL=Qwen/Qwen2.5-Coder-32B-Instruct-AWQ
```

---

## Phase 4: Start Local Model Servers (vLLM)

Choose ONE of these configurations based on your needs:

### Option A: Qwen 2.5 Coder 32B (Recommended - Daily Driver)

Best for coding tasks. Uses ~18.5GB VRAM.

```powershell
python -m vllm.entrypoints.openai.api_server `
    --model Qwen/Qwen2.5-Coder-32B-Instruct-AWQ `
    --quantization awq `
    --dtype half `
    --gpu-memory-utilization 0.90 `
    --max-model-len 32768 `
    --port 8000
```

### Option B: DeepSeek R1 Distill 70B (Deep Reasoning)

For complex reasoning. Uses nearly all 44GB VRAM.

```powershell
python -m vllm.entrypoints.openai.api_server `
    --model casperhansen/deepseek-r1-distill-llama-70b-awq `
    --quantization awq `
    --dtype half `
    --gpu-memory-utilization 0.98 `
    --enforce-eager `
    --max-model-len 8192 `
    --port 8001
```

### Option C: Mistral Small 24B (Creative/Chat)

Excellent for creative writing. Uses ~14.5GB VRAM.

```powershell
python -m vllm.entrypoints.openai.api_server `
    --model casperhansen/mistral-small-24b-instruct-2501-awq `
    --quantization awq `
    --dtype half `
    --gpu-memory-utilization 0.90 `
    --max-model-len 32768 `
    --port 8002
```

### Option D: Llama 3.1 8B (Ultra-Fast)

For quick responses. Uses only ~5.5GB VRAM.

```powershell
python -m vllm.entrypoints.openai.api_server `
    --model hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4 `
    --quantization awq `
    --dtype half `
    --gpu-memory-utilization 0.90 `
    --max-model-len 32768 `
    --port 8003
```

### Verify vLLM Server

```powershell
# Test endpoint
curl http://localhost:8000/v1/models

# Test generation
curl http://localhost:8000/v1/chat/completions `
    -H "Content-Type: application/json" `
    -d '{"model": "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ", "messages": [{"role": "user", "content": "Hello"}]}'
```

---

## Phase 5: Hybrid Mode with llama.cpp (Optional)

For models that don't fit in VRAM (405B, 671B), use CPU+GPU hybrid mode.

### 5.1 Download llama.cpp

```powershell
# Download pre-built Windows release with CUDA
# From: https://github.com/ggerganov/llama.cpp/releases
# Get: llama-bXXXX-bin-win-cuda-cu12.2.0-x64.zip
```

### 5.2 Download GGUF Model

```powershell
# Example: Download DeepSeek R1 Q4_K_M
# From: https://huggingface.co/bartowski/DeepSeek-R1-GGUF
# Warning: ~400GB download!
```

### 5.3 Run llama-server

```powershell
# Start with 40 layers on GPU, rest on CPU RAM
.\llama-server.exe `
    -m DeepSeek-R1.Q4_K_M.gguf `
    -ngl 40 `
    -c 8192 `
    --host 0.0.0.0 --port 8004
```

**Performance Note:** Hybrid mode runs at 1-3 tokens/sec but provides maximum model intelligence.

---

## Phase 6: Deploy MCP Server

### 6.1 Start the Server

```powershell
# Activate venv
cd C:\Users\$env:USERNAME\Projects\tt_malmo\tt_malmo_mcp_server
.\venv\Scripts\Activate.ps1

# Load environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}

# Start server
python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8080
```

### 6.2 Verify Deployment

```powershell
# Health check
curl http://localhost:8080/health

# List available providers
curl http://localhost:8080/providers
```

---

## Phase 7: Set Up Malmo/Minecraft

### 7.1 Install Java 8

```powershell
# Download and install Java 8 JDK
winget install EclipseAdoptium.Temurin.8.JDK

# Verify
java -version  # Should show 1.8.x
```

### 7.2 Build Malmo Minecraft Mod

```powershell
# Navigate to Malmo Minecraft directory
cd C:\Users\$env:USERNAME\Projects\tt_malmo\malmo\Minecraft

# Set JAVA_HOME
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-8.0.xxx"

# Build with Gradle
.\gradlew.bat setupDecompWorkspace
.\gradlew.bat build
```

### 7.3 Launch Minecraft

```powershell
# Start Minecraft client
cd C:\Users\$env:USERNAME\Projects\tt_malmo\malmo\Minecraft
.\launchClient.bat -port 9000 -env
```

---

## Testing the Deployment

### Test 1: vLLM Server

```powershell
curl http://localhost:8000/v1/models
```

### Test 2: MCP Server Health

```powershell
curl http://localhost:8080/health
```

### Test 3: Create Agent with Local LLM

```powershell
curl -X POST http://localhost:8080/agents `
    -H "Content-Type: application/json" `
    -d '{"name":"LocalAgent","llm_type":"vllm","role":0,"traits":["curious"]}'
```

### Test 4: Run Test Suite

```powershell
pytest tests/ -v
```

---

## Troubleshooting

### vLLM Won't Start

```powershell
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU memory
nvidia-smi

# Try with lower memory utilization
python -m vllm.entrypoints.openai.api_server --model MODEL --gpu-memory-utilization 0.80
```

### Out of Memory (OOM)

- Reduce `--max-model-len` (e.g., 8192 instead of 32768)
- Reduce `--gpu-memory-utilization` (e.g., 0.85)
- Use a smaller model
- Add `--enforce-eager` flag

### Model Download Issues

```powershell
# Set Hugging Face cache directory
$env:HF_HOME = "D:\hf_cache"

# Login to Hugging Face (for gated models)
huggingface-cli login
```

### Port Already in Use

```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F
```

---

## Multi-Model Configurations

What fits in 44GB VRAM simultaneously:

| Configuration | Total VRAM | Use Case |
|--------------|-----------|----------|
| Qwen 32B + Mistral 24B | 33GB | Coding + Creative |
| Qwen 32B + Llama 8B | 24GB | Coding + Fast |
| Mistral 24B + Llama 8B | 20GB | Creative + Fast |
| Qwen 32B + Mistral 24B + Llama 8B | 38.5GB | Full multi-model |
| DeepSeek R1 70B alone | 40GB | Deep reasoning only |

To run multiple models, start each vLLM server in a separate terminal on different ports.

---

## Storage Considerations

With 76GB free disk space:

| Item | Size |
|------|------|
| Qwen 2.5 Coder 32B (AWQ) | ~18GB |
| DeepSeek R1 Distill 70B (AWQ) | ~40GB |
| Mistral Small 24B (AWQ) | ~14GB |
| Llama 3.1 8B (AWQ) | ~5GB |
| Repository + venv | ~4GB |
| **Total for all 4** | ~81GB |

**Recommendation:** Download 2-3 models initially, swap as needed.

---

## Quick Reference

### Start vLLM (Qwen Coder)

```powershell
python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2.5-Coder-32B-Instruct-AWQ --quantization awq --port 8000
```

### Start MCP Server

```powershell
python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8080
```

### Start Minecraft

```powershell
.\launchClient.bat -port 9000 -env
```

### Create Agent

```powershell
curl -X POST http://localhost:8080/agents -H "Content-Type: application/json" -d '{"name":"TestAgent","llm_type":"vllm"}'
```
