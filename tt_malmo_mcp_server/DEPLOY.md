# CREATE Cloud Deployment Guide

Complete guide for deploying the Malmo MCP Server on King's College London CREATE Cloud infrastructure.

## Prerequisites

- CREATE Cloud account with project access
- API keys for Gemini (and optionally Claude)
- SSH key configured in CREATE Cloud
- Basic knowledge of Linux and Docker

## Step 1: Create VM Instance

### 1.1 Log into CREATE Cloud

Visit: https://create.kcl.ac.uk/ (or your specific CREATE Cloud URL)

### 1.2 Launch Instance

```
1. Click "Instances" → "Launch Instance"
2. Details:
   - Instance Name: malmo-mcp-server
   - Description: Multi-agent Malmo benchmarking system
   
3. Source:
   - Select Boot Source: Image
   - Image: Ubuntu 20.04 LTS
   - Volume Size: 50 GB
   
4. Flavor:
   - Select: m1.large (or equivalent)
   - 8 GB RAM minimum
   - 4 vCPUs minimum
   
5. Network:
   - Select your project network
   
6. Security Groups:
   - Create/select group allowing:
     - Port 22 (SSH)
     - Port 8000 (MCP Server)
     - Ports 9000-9010 (Malmo servers)
   
7. Key Pair:
   - Select your SSH key
   
8. Launch Instance
```

### 1.3 Assign Floating IP

```
1. Navigate to "Instances"
2. Find your instance
3. Click "Associate Floating IP"
4. Select or create new floating IP
5. Note the IP address (e.g., 192.168.1.100)
```

## Step 2: Initial Server Setup

### 2.1 SSH into VM

```bash
ssh ubuntu@YOUR_FLOATING_IP
```

### 2.2 Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.3 Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
exit
ssh ubuntu@YOUR_FLOATING_IP

# Verify Docker installation
docker --version
```

### 2.4 Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

## Step 3: Deploy Application

### 3.1 Clone Repository

```bash
cd ~
git clone https://github.com/ricardotwumasi/tt_malmo.git
cd tt_malmo/tt_malmo_mcp_server
```

### 3.2 Configure Environment

```bash
# Create .env file from example
cp .env.example .env

# Edit configuration
nano .env
```

Add your configuration:

```env
# API Keys (REQUIRED)
GOOGLE_API_KEY=your_actual_gemini_api_key_here
ANTHROPIC_API_KEY=your_claude_key_if_you_have_one

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Malmo Configuration
MALMO_PORT=9000
DEFAULT_MISSION=mobchase_single_agent.xml

# Agent Configuration
DECISION_INTERVAL=5.0
MAX_STEPS=1000

# Deployment
ENVIRONMENT=production
DEBUG=false
```

Save and exit (Ctrl+X, Y, Enter)

### 3.3 Build Docker Images

```bash
# This may take 10-15 minutes
docker-compose build
```

### 3.4 Start Services

```bash
# Start all services in background
docker-compose up -d

# Check status
docker-compose ps

# Should show:
# - malmo-mcp-server (running)
# - malmo-server-1 through malmo-server-5 (running)
```

### 3.5 Verify Deployment

```bash
# Check MCP server health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"..."}

# Check logs
docker-compose logs -f mcp-server

# Press Ctrl+C to exit logs
```

## Step 4: Test Multi-Agent Setup

### 4.1 Create Test Agents

```bash
# Create 5 agents
for i in {0..4}; do
  curl -X POST http://localhost:8000/agents \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"Agent_Gemini_$i\",
      \"llm_provider\": \"gemini\",
      \"model\": \"gemini-2.5-flash\",
      \"role\": $i,
      \"traits\": [\"curious\", \"strategic\"]
    }"
  echo ""
done
```

### 4.2 List Agents

```bash
curl http://localhost:8000/agents | python3 -m json.tool
```

### 4.3 Start Agent Decision Loop

```bash
# Get first agent ID from previous command, then:
AGENT_ID="paste-agent-id-here"

curl -X POST http://localhost:8000/agents/$AGENT_ID/start
```

### 4.4 Monitor Agent Activity

```bash
# Watch agent state
watch -n 2 "curl -s http://localhost:8000/agents/$AGENT_ID/state | python3 -m json.tool"

# Or check logs
docker-compose logs -f mcp-server
```

## Step 5: External Access

### 5.1 Configure Security Group

Ensure your CREATE Cloud security group allows:
- TCP 8000 from your IP (or 0.0.0.0/0 for public access)
- TCP 22 for SSH

### 5.2 Test External Access

From your local machine:

```bash
curl http://YOUR_FLOATING_IP:8000/health
```

### 5.3 Access API Documentation

Visit in browser:
```
http://YOUR_FLOATING_IP:8000/docs
```

## Step 6: Production Configuration

### 6.1 Enable HTTPS (Optional)

```bash
# Install nginx
sudo apt install nginx certbot python3-certbot-nginx

# Configure nginx reverse proxy
sudo nano /etc/nginx/sites-available/malmo-mcp

# Add configuration for your domain
# Then enable SSL with Let's Encrypt
sudo certbot --nginx -d your-domain.kcl.ac.uk
```

### 6.2 Set Up System Service

Create systemd service for automatic restart:

```bash
sudo nano /etc/systemd/system/malmo-mcp.service
```

```ini
[Unit]
Description=Malmo MCP Server
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/tt_malmo/tt_malmo_mcp_server
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
```

Enable service:

```bash
sudo systemctl enable malmo-mcp
sudo systemctl start malmo-mcp
```

### 6.3 Configure Log Rotation

```bash
sudo nano /etc/logrotate.d/malmo-mcp
```

```
/home/ubuntu/tt_malmo/tt_malmo_mcp_server/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## Step 7: Monitoring and Maintenance

### 7.1 Check System Resources

```bash
# CPU and memory usage
docker stats

# Disk usage
df -h

# Docker disk usage
docker system df
```

### 7.2 View Logs

```bash
# All services
docker-compose logs --tail=100 -f

# Specific service
docker-compose logs --tail=100 -f mcp-server
docker-compose logs --tail=100 -f malmo-server-1

# Search logs
docker-compose logs | grep ERROR
```

### 7.3 Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart mcp-server
docker-compose restart malmo-server-1
```

### 7.4 Update Application

```bash
cd ~/tt_malmo/tt_malmo_mcp_server

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose down
docker-compose up -d
```

## Troubleshooting

### Issue: Container won't start

```bash
# Check logs
docker-compose logs mcp-server

# Check configuration
docker-compose config

# Remove and recreate
docker-compose down
docker-compose up -d
```

### Issue: Out of memory

```bash
# Check memory
free -h

# Restart services to free memory
docker-compose restart

# Or increase VM size in CREATE Cloud
```

### Issue: Port already in use

```bash
# Find process using port
sudo lsof -i :8000

# Kill process if needed
sudo kill -9 <PID>

# Or change port in .env and docker-compose.yml
```

### Issue: Malmo connection timeout

```bash
# Restart Malmo servers
docker-compose restart malmo-server-1

# Check Malmo logs
docker-compose logs malmo-server-1

# Verify port is accessible
nc -zv localhost 9000
```

## Performance Tuning

### For Multiple Agents

```yaml
# In docker-compose.yml, adjust resources:
services:
  mcp-server:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          memory: 2G
```

### For Better Responsiveness

```env
# In .env, adjust timing:
DECISION_INTERVAL=3.0  # Faster decisions (default: 5.0)
```

## Backup and Recovery

### Backup Data

```bash
# Backup agent data and metrics
tar -czf backup-$(date +%Y%m%d).tar.gz \
  agent_data/ \
  metrics/ \
  .env

# Download to local machine
scp ubuntu@YOUR_IP:backup-*.tar.gz ./
```

### Restore Data

```bash
# Upload backup
scp backup-YYYYMMDD.tar.gz ubuntu@YOUR_IP:~/

# Extract
tar -xzf backup-YYYYMMDD.tar.gz
```

## Security Best Practices

1. Keep API keys in .env file only (never commit to git)
2. Use security groups to restrict access
3. Keep system and Docker updated
4. Monitor logs for suspicious activity
5. Use HTTPS for production deployment
6. Rotate API keys periodically

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Consult README.md troubleshooting section
3. Contact CREATE support: support@er.kcl.ac.uk
4. GitHub issues: https://github.com/ricardotwumasi/tt_malmo/issues

## Next Steps

- Implement benchmarking metrics
- Set up monitoring dashboard
- Configure automated testing
- Scale to 10+ agents
- Integrate with research workflow
