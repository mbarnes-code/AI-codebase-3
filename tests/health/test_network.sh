#!/bin/bash
# test_network.sh - Test connectivity between Jane and Motoko servers

echo "=== Network Connectivity Test ==="
echo "Testing connectivity between Jane (192.168.1.17) and Motoko (192.168.1.12)"
echo

# Test if Motoko server is reachable
echo "1. Testing if Motoko server is reachable..."
if curl -s --connect-timeout 5 http://192.168.1.12:8000/health > /dev/null; then
    echo "✅ Motoko server is reachable at 192.168.1.12:8000"
    
    # Test health endpoint
    echo "2. Testing Motoko health endpoint..."
    response=$(curl -s http://192.168.1.12:8000/health)
    echo "Health response: $response"
    
    # Test Jane's health check endpoint
    echo "3. Testing Jane's health check endpoint..."
    if command -v node >/dev/null 2>&1; then
        echo "Node.js found, you can test Jane's health endpoint at:"
        echo "http://192.168.1.17:3001/api/ai/health"
    else
        echo "Node.js not found on this machine"
    fi
    
else
    echo "❌ Cannot reach Motoko server at 192.168.1.12:8000"
    echo "Please ensure:"
    echo "  - Motoko server is running"
    echo "  - Firewall allows port 8000"
    echo "  - Network routing is correct"
fi

echo
echo "=== Manual Test Commands ==="
echo "Test Motoko directly:"
echo "curl http://192.168.1.12:8000/health"
echo
echo "Test Jane's health check:"
echo "curl http://192.168.1.17:3001/api/ai/health"
echo
echo "Test deck building:"
echo 'curl -X POST http://192.168.1.17:3001/api/ai/build-deck \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d '"'"'{"commander": "Atraxa, Praetor'"'"'s Voice"}'
