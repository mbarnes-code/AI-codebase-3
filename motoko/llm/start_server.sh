#!/bin/bash
# motoko/llm/start_server.sh
# Script to start the Motoko LLM server

echo "Starting Motoko LLM Server..."
echo "Server will be accessible at http://192.168.1.12:8000"
echo "Health check: http://192.168.1.12:8000/health"
echo "Generate endpoint: http://192.168.1.12:8000/generate"

# Check if running in Docker or directly
if [ "$1" = "docker" ]; then
    echo "Building and running with Docker..."
    docker build -t motoko-llm-server .
    docker run -p 8000:8000 --name motoko-llm motoko-llm-server
else
    echo "Running directly with Python..."
    echo "Make sure you have installed: pip install -r requirements.txt"
    python llm_server.py
fi
