#!/bin/bash

# Setup API Key Script
# This script helps you configure your Gemini API key

echo "=================================================="
echo "  Malmo MCP Server - API Key Setup"
echo "=================================================="
echo ""

if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

echo "Please paste your Google Gemini API key:"
echo "(The key will not be displayed as you type)"
echo ""
read -s API_KEY

if [ -z "$API_KEY" ]; then
    echo "Error: No API key provided"
    exit 1
fi

# Update the .env file
sed -i.bak "s/GOOGLE_API_KEY=.*/GOOGLE_API_KEY=$API_KEY/" .env

echo ""
echo "✅ API key configured successfully!"
echo ""
echo "Your API key has been saved to .env"
echo "You can now run the MCP server with:"
echo ""
echo "  python -m uvicorn mcp_server.server:app --reload"
echo ""
echo "=================================================="
