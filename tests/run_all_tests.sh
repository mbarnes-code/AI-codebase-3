#!/bin/bash

# 🧪 Jane AI Platform - Master Test Runner
# This script runs all test categories in the correct order

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}🧪 Jane AI Platform - Master Test Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${YELLOW}Running: $test_name${NC}"
    echo "Command: $test_command"
    echo "----------------------------------------"
    
    if $test_command; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        ((PASSED_TESTS++))
        return 0
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        ((FAILED_TESTS++))
        return 1
    fi
    ((TOTAL_TESTS++))
    echo ""
}

# Change to project root directory
cd "$(dirname "$0")/.."

echo -e "${BLUE}📋 Pre-flight Checks${NC}"
echo "----------------------------------------"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if required files exist
if [[ ! -f ".env" ]]; then
    echo -e "${YELLOW}⚠️  .env file not found. Running setup-secrets.sh...${NC}"
    ./setup-secrets.sh
fi

echo -e "${GREEN}✅ Pre-flight checks completed${NC}"
echo ""

# 1. Build Tests (must run first)
echo -e "${BLUE}🏗️  Build Tests${NC}"
echo "========================================"
run_test "Docker Build Validation" "./tests/build/build_test.sh"
((TOTAL_TESTS++))

# 2. Health Tests (check basic connectivity)
echo -e "${BLUE}🩺 Health Tests${NC}"
echo "========================================"
run_test "Service Health Check" "./tests/health/health-check.sh"
((TOTAL_TESTS++))
run_test "Network Connectivity Test" "./tests/health/test_network.sh"  
((TOTAL_TESTS++))

# 3. Integration Tests (comprehensive system testing)
echo -e "${BLUE}🔧 Integration Tests${NC}"
echo "========================================"
run_test "Quick Validation Test" "./tests/integration/quick_test.sh"
((TOTAL_TESTS++))
run_test "Service Startup Test" "./tests/integration/startup_test.sh"
((TOTAL_TESTS++))
run_test "API Endpoint Test" "cd ./tests/integration && python api_test.py"
((TOTAL_TESTS++))
run_test "Enhanced Integration Test" "./tests/integration/integration_test_new.sh"
((TOTAL_TESTS++))

# 4. Unit Tests (if any exist)
echo -e "${BLUE}🧩 Unit Tests${NC}"
echo "========================================"

# Check for Python unit tests
if find ./tests/unit -name "*.py" -type f | grep -q .; then
    # Run spellbook unit tests if they exist
    if [[ -d "./tests/unit/spellbook" ]]; then
        run_test "Spellbook Unit Tests" "cd ./tests/unit/spellbook && python -m pytest -v"
        ((TOTAL_TESTS++))
    fi
    
    # Run spellbook-client unit tests if they exist
    if [[ -d "./tests/unit/spellbook-client" ]]; then
        run_test "Spellbook Client Unit Tests" "cd ./tests/unit/spellbook-client && python -m pytest -v"
        ((TOTAL_TESTS++))
    fi
    
    # Run website unit tests if they exist
    if [[ -d "./tests/unit/website" ]]; then
        run_test "Website Unit Tests" "cd ./tests/unit/website && python -m pytest tests.py -v"
        ((TOTAL_TESTS++))
    fi
    
    # Run common unit tests if they exist
    if [[ -d "./tests/unit/common" ]]; then
        run_test "Common Utils Unit Tests" "cd ./tests/unit/common && python -m pytest -v"
        ((TOTAL_TESTS++))
    fi
else
    echo -e "${YELLOW}⚠️  No unit tests found in ./tests/unit/${NC}"
    echo "Unit tests will be added as development continues."
fi

# Summary
echo ""
echo -e "${BLUE}📊 Test Summary${NC}"
echo "========================================"
echo -e "Total Tests: ${TOTAL_TESTS}"
echo -e "${GREEN}Passed: ${PASSED_TESTS}${NC}"
echo -e "${RED}Failed: ${FAILED_TESTS}${NC}"
echo ""

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "${GREEN}🎉 All tests passed successfully!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the output above.${NC}"
    exit 1
fi
