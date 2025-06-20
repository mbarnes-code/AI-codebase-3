#!/bin/bash

echo "🚀 Jane AI Platform Service Build Test"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0

build_service() {
    local name="$1"
    local path="$2"
    
    echo -e "${BLUE}Building $name...${NC}"
    
    if cd "$path" && docker build -t "test-$name" . > "/tmp/${name}_build.log" 2>&1; then
        echo -e "${GREEN}✅ SUCCESS: $name builds successfully${NC}"
        docker rmi "test-$name" > /dev/null 2>&1
        ((PASS++))
    else
        echo -e "${RED}❌ FAILED: $name build failed${NC}"
        echo "   Log: /tmp/${name}_build.log"
        ((FAIL++))
    fi
    cd - > /dev/null
}

# Build all main services
build_service "adhd-support" "./Jane/adhd-support"
build_service "auth-service" "./Jane/auth-service"
build_service "mcp-server" "./Jane/mcp-server"

echo ""
echo -e "${YELLOW}Build Summary${NC}"
echo "============="
echo -e "Services tested: $((PASS + FAIL))"
echo -e "${GREEN}Successful builds: $PASS${NC}"
echo -e "${RED}Failed builds: $FAIL${NC}"

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 All services build successfully!${NC}"
else
    echo -e "${RED}⚠️ $FAIL service(s) failed to build.${NC}"
fi
