# Linux Server Deployment Guide

This guide covers deploying the Malmo AI Benchmark platform to a Linux server (Ubuntu/Debian).

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ server
- At least 4GB RAM, 8GB recommended
- 20GB disk space
- Root or sudo access
- API keys for LLM providers

## Quick Deploy (Docker)

The fastest way to deploy is using Docker:

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in

# 2. Clone the repository
git clone https://github.com/ricardotwumasi/tt_malmo.git
cd tt_malmo/tt_malmo_mcp_server

# 3. Create environment file
cp .env.example .env
nano .env  # Add your API keys

# 4. Start the full stack
docker compose -f deployment/docker-compose.yml up -d

# 5. Check status
docker compose -f deployment/docker-compose.yml ps
docker compose -f deployment/docker-compose.yml logs -f
```

Services will be available at:
- MCP Server: http://your-server:8000
- API Docs: http://your-server:8000/docs
- Malmo: localhost:9000 (internal)

## Manual Installation (Without Docker)

### Step 1: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and build tools
sudo apt install -y python3.11 python3.11-venv python3-pip git curl

# Install Java 8 (for Minecraft)
sudo apt install -y openjdk-8-jdk

# Install PostgreSQL (optional, for metrics storage)
sudo apt install -y postgresql postgresql-contrib

# Install display server for headless Minecraft
sudo apt install -y xvfb x11vnc
```

### Step 2: Clone and Setup

```bash
# Clone repository
git clone https://github.com/ricardotwumasi/tt_malmo.git
cd tt_malmo/tt_malmo_mcp_server

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
nano .env
```

Required environment variables:
```bash
# At least one LLM provider (Gemini recommended)
GOOGLE_API_KEY=your_gemini_api_key

# Optional additional providers
OPENROUTER_API_KEY=your_openrouter_key
CEREBRAS_API_KEY=your_cerebras_key

# Database (optional)
DATABASE_URL=postgresql://user:password@localhost:5432/malmo_benchmarks
```

### Step 4: Setup PostgreSQL (Optional)

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE USER malmo WITH PASSWORD 'your_secure_password';
CREATE DATABASE malmo_benchmarks OWNER malmo;
GRANT ALL PRIVILEGES ON DATABASE malmo_benchmarks TO malmo;
EOF

# Update .env with database URL
echo "DATABASE_URL=postgresql://malmo:your_secure_password@localhost:5432/malmo_benchmarks" >> .env
```

### Step 5: Run Tests

```bash
source venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
pytest tests/ -v
```

### Step 6: Start the Server

#### Option A: Direct Run (Development)

```bash
source venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000
```

#### Option B: Systemd Service (Production)

Create systemd service file:

```bash
sudo tee /etc/systemd/system/mcp-server.service << EOF
[Unit]
Description=Malmo MCP Server
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
EnvironmentFile=$(pwd)/.env
ExecStart=$(pwd)/venv/bin/python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable mcp-server
sudo systemctl start mcp-server

# Check status
sudo systemctl status mcp-server
```

### Step 7: Setup Minecraft with Malmo (Optional)

For full Minecraft integration:

```bash
# Start virtual display
export DISPLAY=:99
Xvfb :99 -screen 0 1280x720x24 &

# Build Minecraft with Malmo
cd ../malmo/Minecraft
./gradlew setupDecompWorkspace
./gradlew build

# Start Minecraft
./launchClient.sh -port 9000 -env &

# Return to MCP server directory
cd ../../tt_malmo_mcp_server
```

## Firewall Configuration

```bash
# Allow HTTP traffic
sudo ufw allow 8000/tcp

# If using VNC for debugging
sudo ufw allow 5900/tcp

# Enable firewall
sudo ufw enable
```

## Nginx Reverse Proxy (Optional)

For production with SSL:

```bash
# Install Nginx
sudo apt install -y nginx certbot python3-certbot-nginx

# Create config
sudo tee /etc/nginx/sites-available/mcp-server << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/mcp-server /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Monitoring

### View Logs

```bash
# Systemd service logs
sudo journalctl -u mcp-server -f

# Docker logs
docker compose -f deployment/docker-compose.yml logs -f
```

### Health Check

```bash
curl http://localhost:8000/health
```

### API Status

```bash
# List agents
curl http://localhost:8000/agents

# Server metrics (if enabled)
curl http://localhost:8000/metrics
```

## Troubleshooting

### Port already in use

```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Database connection failed

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U malmo -d malmo_benchmarks
```

### API key errors

```bash
# Verify environment variables are loaded
env | grep API_KEY

# Test Gemini connection
python test_gemini.py
```

### Minecraft won't start

```bash
# Check Java version
java -version  # Should be 1.8.x

# Check display
echo $DISPLAY  # Should be :99 or similar

# Check Xvfb
ps aux | grep Xvfb
```

## CREATE Cloud (KCL) Specific

For deployment on KCL's CREATE Cloud:

1. Request a VM with Ubuntu 22.04
2. Ensure ports 8000 and 5432 are open
3. Follow the manual installation steps above
4. Use systemd for service management

CREATE Cloud docs: https://docs.er.kcl.ac.uk/

## Next Steps

1. Test the API: `curl http://your-server:8000/health`
2. Create agents via API or dashboard
3. Monitor agent decisions in logs
4. Collect benchmarking metrics
