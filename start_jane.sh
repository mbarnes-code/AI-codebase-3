#!/bin/bash
# start_jane.sh - Start Jane frontend server

cd /workspaces/AI-codebase-3/Jane/commander-spellbook-site-main

echo "=== Starting Jane Frontend Server ==="
echo "Server will be accessible at http://192.168.1.17:3001"
echo "Environment: Production"
echo "LLM Server: http://192.168.1.12:8000"
echo

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build the application
echo "Building application..."
npm run build

# Start the server
echo "Starting Jane server..."
NODE_ENV=production npm start -- -p 3001
