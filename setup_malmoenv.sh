#!/bin/bash

echo "=================================================="
echo "  Setting up MalmoEnv (Python interface)"
echo "=================================================="
echo ""

# Ensure we're in the malmo directory
cd "$(dirname "$0")"

# Step 1: Create version.properties file (this was missing!)
echo "📝 Creating version.properties..."
cd Minecraft
(echo -n "malmomod.version=" && cat ../VERSION) > ./src/main/resources/version.properties
echo "✅ version.properties created"

# Step 2: Install MalmoEnv Python package
echo ""
echo "📦 Installing MalmoEnv Python package..."
cd ../MalmoEnv
pip3 install gymnasium lxml numpy pillow
python3 setup.py install --user

echo ""
echo "=================================================="
echo "✅ MalmoEnv setup complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Launch Minecraft (Terminal 1):"
echo "   cd Minecraft"
echo "   ./launchClient.sh -port 9000 -env"
echo ""
echo "2. Test MalmoEnv (Terminal 2):"
echo "   cd MalmoEnv"
echo "   python3 run.py --mission missions/mobchase_single_agent.xml --port 9000 --episodes 1"
echo ""
echo "=================================================="
