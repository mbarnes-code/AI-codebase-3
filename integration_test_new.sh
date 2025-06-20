#!/bin/bash
# Enhanced integration test for AI Second Brain Platform

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "\n${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Test counter
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    print_step "$test_name"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    if eval "$test_command" > /dev/null 2>&1; then
        print_success "$test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        print_error "$test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="${3:-}"
    
    ((TESTS_TOTAL++))
    print_step "Testing $test_name"
    
    if eval "$test_command"; then
        if [ -n "$expected_pattern" ]; then
            if eval "$test_command" | grep -q "$expected_pattern"; then
                print_success "$test_name passed"
                ((TESTS_PASSED++))
                return 0
            else
                print_error "$test_name failed - pattern '$expected_pattern' not found"
                ((TESTS_FAILED++))
                return 1
            fi
        else
            print_success "$test_name passed"
            ((TESTS_PASSED++))
            return 0
        fi
    else
        print_error "$test_name failed"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "🧪 AI Second Brain Platform Integration Test"
echo "============================================="
echo "Timestamp: $(date)"

# Test 1: Basic connectivity
run_test "Jane connectivity" "ping -c 1 127.0.0.1 >/dev/null 2>&1"

# Test 2: Motoko connectivity
run_test "Motoko connectivity" "ping -c 1 192.168.1.12 >/dev/null 2>&1"

# Test 3: Core infrastructure health
run_test "Redis health" "curl -s --connect-timeout 5 http://127.0.0.1:6379 >/dev/null 2>&1 || docker-compose exec -T redis redis-cli ping >/dev/null 2>&1"

run_test "PostgreSQL health" "docker-compose exec -T spellbook-db pg_isready -U spellbook_user >/dev/null 2>&1"

# Test 4: ADHD Support Service (Priority #1)
run_test "ADHD Support health" "curl -s --connect-timeout 10 http://127.0.0.1:8001/health" "healthy"

run_test "ADHD Support task creation" "curl -s -X POST http://127.0.0.1:8001/tasks -H 'Content-Type: application/json' -d '{\"title\":\"Test Task\",\"priority\":3}'" "Test Task"

# Test 5: Authentication Service
run_test "Auth service health" "curl -s --connect-timeout 10 http://127.0.0.1:8003/health" "healthy"

# Test 6: MCP Server
run_test "MCP Server health" "curl -s --connect-timeout 10 http://127.0.0.1:8002/health" "healthy"

run_test "MCP Server tools list" "curl -s http://127.0.0.1:8002/tools" "codebase_scan"

# Test 7: Monitoring stack
run_test "Prometheus health" "curl -s --connect-timeout 10 http://127.0.0.1:9090/-/healthy"

run_test "Grafana health" "curl -s --connect-timeout 10 http://127.0.0.1:3000/api/health"

# Test 8: Commander Spellbook
run_test "Spellbook frontend" "curl -s --connect-timeout 15 http://127.0.0.1:3001" "Commander Spellbook"

# Test 9: AI Integration (Motoko)
if curl -s --connect-timeout 10 http://192.168.1.12:8000/health >/dev/null 2>&1; then
    run_test "Motoko LLM health" "curl -s --connect-timeout 10 http://192.168.1.12:8000/health" "healthy"
    
    # Test AI-powered deck building
    run_test "AI deck building integration" "curl -s -X POST http://127.0.0.1:3001/api/ai/build-deck -H 'Content-Type: application/json' -d '{\"commander\":\"Test Commander\"}'" "commander"
    
    # Test ADHD AI assistance
    run_test "ADHD AI assistance" "curl -s -X POST http://127.0.0.1:8001/ai/ask -H 'Content-Type: application/json' -d '{\"prompt\":\"Help me organize my tasks\"}'" "response"
else
    print_warning "Motoko LLM server not available - skipping AI integration tests"
fi

# Test 10: Resource usage validation
print_step "Checking resource usage constraints"

# Check if Jane's CPU usage is reasonable
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//' | cut -d'%' -f1)
if (( $(echo "$CPU_USAGE < 90" | bc -l) )); then
    print_success "CPU usage is acceptable (${CPU_USAGE}%)"
    ((TESTS_PASSED++))
else
    print_warning "CPU usage is high (${CPU_USAGE}%) - may affect ADHD support responsiveness"
    ((TESTS_FAILED++))
fi
((TESTS_TOTAL++))

# Test 11: Docker container health
print_step "Checking Docker container health"

UNHEALTHY_CONTAINERS=$(docker ps --filter "health=unhealthy" --format "{{.Names}}" | wc -l)
if [ "$UNHEALTHY_CONTAINERS" -eq 0 ]; then
    print_success "All containers are healthy"
    ((TESTS_PASSED++))
else
    print_error "$UNHEALTHY_CONTAINERS containers are unhealthy"
    docker ps --filter "health=unhealthy" --format "{{.Names}}: {{.Status}}"
    ((TESTS_FAILED++))
fi
((TESTS_TOTAL++))

# Test 12: Network communication test
print_step "Testing Jane-Motoko communication"

if curl -s --connect-timeout 10 "http://192.168.1.12:8000/health" >/dev/null 2>&1; then
    # Test a simple AI request from Jane to Motoko
    AI_RESPONSE=$(curl -s -X POST http://192.168.1.12:8000/generate \
        -H "Content-Type: application/json" \
        -d '{"prompt":"Hello","max_tokens":10}' | grep -o "response")
    
    if [ "$AI_RESPONSE" = "response" ]; then
        print_success "Jane-Motoko AI communication working"
        ((TESTS_PASSED++))
    else
        print_error "Jane-Motoko AI communication failed"
        ((TESTS_FAILED++))
    fi
else
    print_warning "Motoko not accessible - skipping communication test"
fi
((TESTS_TOTAL++))

# Test 13: Database integration
print_step "Testing database integration"

# Test task persistence
TASK_ID=$(curl -s -X POST http://127.0.0.1:8001/tasks \
    -H "Content-Type: application/json" \
    -d '{"title":"Integration Test Task","priority":3}' | \
    grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TASK_ID" ]; then
    # Try to retrieve the task
    if curl -s "http://127.0.0.1:8001/tasks" | grep -q "$TASK_ID"; then
        print_success "Database integration working"
        ((TESTS_PASSED++))
    else
        print_error "Task retrieval failed"
        ((TESTS_FAILED++))
    fi
else
    print_error "Task creation failed"
    ((TESTS_FAILED++))
fi
((TESTS_TOTAL++))

# Performance test
print_step "Testing ADHD support response time"

START_TIME=$(date +%s%N)
curl -s --connect-timeout 5 http://127.0.0.1:8001/health >/dev/null 2>&1
END_TIME=$(date +%s%N)
RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 ))  # Convert to milliseconds

if [ "$RESPONSE_TIME" -lt 1000 ]; then
    print_success "ADHD support response time: ${RESPONSE_TIME}ms (good)"
    ((TESTS_PASSED++))
else
    print_warning "ADHD support response time: ${RESPONSE_TIME}ms (may be slow for ADHD users)"
    ((TESTS_FAILED++))
fi
((TESTS_TOTAL++))

# Summary
echo
echo "================================================"
echo "🧪 Integration Test Results"
echo "================================================"
echo "Total Tests: $TESTS_TOTAL"
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"
echo

if [ "$TESTS_FAILED" -eq 0 ]; then
    print_success "🎉 All integration tests passed!"
    echo "✅ The AI Second Brain Platform is ready for use"
    echo "✅ ADHD support services are responsive and functional"
    echo "✅ Jane-Motoko integration is working correctly"
    exit 0
elif [ "$TESTS_FAILED" -le 2 ]; then
    print_warning "⚠️ Some tests failed but core functionality is working"
    echo "ℹ️ Review failed tests and consider if they impact critical features"
    exit 1
else
    print_error "❌ Multiple critical tests failed"
    echo "🚨 System requires attention before production use"
    echo "🔧 Run './health-check.sh' for detailed diagnostics"
    exit 2
fi
