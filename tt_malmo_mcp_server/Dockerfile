# Dockerfile for Malmo MCP Server
# Optimized for CREATE Cloud deployment

FROM ubuntu:20.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    python3-dev \
    openjdk-8-jdk \
    wget \
    git \
    xvfb \
    x11vnc \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libgl1-mesa-glx \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Set Java 8 as default
ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install MalmoEnv
RUN pip3 install malmoenv

# Copy application code
COPY . .

# Create directories for data and logs
RUN mkdir -p /app/logs /app/agent_data /app/metrics

# Expose ports
# 8000: MCP Server API
# 9000-9010: Malmo ports for multi-agent
EXPOSE 8000 9000 9001 9002 9003 9004 9005 9006 9007 9008 9009 9010

# Set environment variables
ENV MALMO_DIR=/app/malmo
ENV MALMOENV_DIR=/app/malmo/MalmoEnv
ENV MISSIONS_DIR=/app/malmo/MalmoEnv/missions
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python3 -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command (can be overridden)
CMD ["python3", "-m", "uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "8000"]
