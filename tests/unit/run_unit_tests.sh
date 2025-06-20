#!/bin/bash

# 🧩 Unit Test Runner for Jane AI Platform
# Runs all unit tests with proper Python environment setup

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧩 Running Unit Tests${NC}"
echo -e "${BLUE}=====================${NC}"
echo ""

# Change to tests directory
cd "$(dirname "$0")"

# Function to run unit tests for a component
run_component_tests() {
    local component="$1"
    local test_dir="./unit/$component"
    
    if [[ ! -d "$test_dir" ]]; then
        echo -e "${YELLOW}⚠️  No tests found for component: $component${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Testing component: $component${NC}"
    echo "----------------------------------------"
    
    cd "$test_dir"
    
    # Check if pytest.ini exists for configuration
    if [[ -f "pytest.ini" ]]; then
        echo "Using pytest configuration from pytest.ini"
        python -m pytest -v --tb=short
    else
        # Run all Python test files
        python -m pytest -v --tb=short
    fi
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ $component tests passed${NC}"
    else
        echo -e "${RED}❌ $component tests failed${NC}"
        return 1
    fi
    
    cd - > /dev/null
    echo ""
}

# Check if pytest is available
if ! python -m pytest --version >/dev/null 2>&1; then
    echo -e "${RED}❌ pytest not found. Installing...${NC}"
    pip install pytest
fi

# Test results tracking
TOTAL_COMPONENTS=0
PASSED_COMPONENTS=0
FAILED_COMPONENTS=0

# Components to test
COMPONENTS=("spellbook" "spellbook-client" "website" "common")

for component in "${COMPONENTS[@]}"; do
    ((TOTAL_COMPONENTS++))
    if run_component_tests "$component"; then
        ((PASSED_COMPONENTS++))
    else
        ((FAILED_COMPONENTS++))
    fi
done

# Summary
echo -e "${BLUE}📊 Unit Test Summary${NC}"
echo "================================"
echo -e "Components tested: ${TOTAL_COMPONENTS}"
echo -e "${GREEN}Passed: ${PASSED_COMPONENTS}${NC}"
echo -e "${RED}Failed: ${FAILED_COMPONENTS}${NC}"
echo ""

if [[ $FAILED_COMPONENTS -eq 0 ]]; then
    echo -e "${GREEN}🎉 All unit tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some unit tests failed.${NC}"
    exit 1
fi
