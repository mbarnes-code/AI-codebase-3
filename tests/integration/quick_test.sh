#!/bin/bash

echo "🧪 Jane AI Platform Comprehensive Test Suite"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
PASS=0
FAIL=0

# Test function
test_item() {
    local name="$1"
    local command="$2"
    
    echo -e "${BLUE}Testing: $name${NC}"
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS: $name${NC}"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL: $name${NC}"
        ((FAIL++))
    fi
}

echo -e "${YELLOW}Phase 1: Configuration Files${NC}"
echo "============================="

test_item "Docker Compose syntax" "docker-compose config --quiet"
test_item "Environment file exists" "test -f .env"
test_item "JWT secret exists" "test -f ./secrets/jwt_secret.txt"
test_item "Postgres password exists" "test -f ./secrets/postgres_password.txt"
test_item "SSL certificate exists" "test -f ./Jane/monitoring/ssl/jane.crt"
test_item "Nginx config exists" "test -f ./Jane/monitoring/nginx.conf"

echo ""
echo -e "${YELLOW}Phase 2: Python Code Validation${NC}"
echo "==============================="

test_item "ADHD Support syntax" "python3 -m py_compile ./Jane/adhd-support/main.py"
test_item "Auth Service syntax" "python3 -m py_compile ./Jane/auth-service/main.py"
test_item "MCP Server syntax" "python3 -m py_compile ./Jane/mcp-server/main.py"

echo ""
echo -e "${YELLOW}Phase 3: Service Builds${NC}"
echo "======================"

# Quick build tests
echo -e "${BLUE}Building ADHD Support service...${NC}"
if cd ./Jane/adhd-support && docker build -t test-adhd . > /tmp/adhd_build.log 2>&1; then
    echo -e "${GREEN}✅ PASS: ADHD Support builds successfully${NC}"
    docker rmi test-adhd > /dev/null 2>&1
    ((PASS++))
else
    echo -e "${RED}❌ FAIL: ADHD Support build failed${NC}"
    echo "Build log saved to /tmp/adhd_build.log"
    ((FAIL++))
fi
cd - > /dev/null

echo ""
echo "============================================="
echo -e "${BLUE}Test Summary${NC}"
echo "============================================="
echo -e "Total: $((PASS + FAIL))"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! System ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}⚠️ Some tests failed. Review issues above.${NC}"
    exit 1
fi
