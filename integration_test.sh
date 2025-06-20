#!/bin/bash
# integration_test.sh - Complete integration test between Jane and Motoko

echo "=== Jane-Motoko Integration Test ==="
echo

# Test 1: Motoko server health
echo "1. Testing Motoko server health..."
motoko_health=$(curl -s --connect-timeout 5 http://192.168.1.12:8000/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Motoko server is responding"
    echo "   Response: $motoko_health"
else
    echo "❌ Motoko server is not responding"
    echo "   Make sure it's running with: cd motoko/llm && ./start_server.sh"
    exit 1
fi

echo

# Test 2: Basic generate endpoint
echo "2. Testing Motoko generate endpoint..."
generate_response=$(curl -s --connect-timeout 10 -X POST http://192.168.1.12:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "model": "llama2"}' 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ Motoko generate endpoint is working"
    echo "   Response length: $(echo "$generate_response" | wc -c) characters"
else
    echo "❌ Motoko generate endpoint failed"
    echo "   This might be normal if Ollama models aren't installed"
fi

echo

# Test 3: Check if Jane is running (if we can access it)
echo "3. Testing Jane server availability..."
jane_response=$(curl -s --connect-timeout 5 http://192.168.1.17:3001 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Jane server is responding"
    
    # Test Jane's health endpoint
    echo "4. Testing Jane's AI health endpoint..."
    jane_health=$(curl -s --connect-timeout 10 http://192.168.1.17:3001/api/ai/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ Jane AI health endpoint is working"
        echo "   Response: $jane_health"
    else
        echo "❌ Jane AI health endpoint failed"
    fi
else
    echo "⚠️  Cannot reach Jane server (this is normal if testing from Motoko)"
    echo "   To test from Jane side, run this script from Jane server"
fi

echo
echo "=== Test Summary ==="
echo "✅ Tests completed"
echo
echo "Next steps:"
echo "1. Ensure both servers are running"
echo "2. Test the full deck building API:"
echo "   curl -X POST http://192.168.1.17:3001/api/ai/build-deck \\"
echo "     -H 'Content-Type: application/json' \\"
echo '     -d '"'"'{"commander": "Atraxa, Praetors'"'"' Voice"}'"'"
echo
echo "3. Monitor logs on both servers for any errors"
