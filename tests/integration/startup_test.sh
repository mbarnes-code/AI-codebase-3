#!/bin/bash

echo "🔥 Jane AI Platform Service Startup Test"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting core services...${NC}"

# Start core infrastructure services first
echo -e "${YELLOW}Phase 1: Starting infrastructure services${NC}"
docker-compose up -d redis spellbook-db vault

echo "Waiting for services to initialize..."
sleep 10

# Check service health
check_service() {
    local name="$1"
    local check_command="$2"
    
    echo -e "${BLUE}Checking $name...${NC}"
    
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ $name is not responding${NC}"
        return 1
    fi
}

echo ""
echo -e "${YELLOW}Phase 2: Health checks${NC}"

# Check Redis
check_service "Redis" "docker-compose exec -T redis redis-cli ping | grep -q PONG"

# Check PostgreSQL
check_service "PostgreSQL" "docker-compose exec -T spellbook-db pg_isready -U spellbook_user"

# Check Vault
check_service "Vault" "curl -s http://127.0.0.1:8200/v1/sys/health"

echo ""
echo -e "${YELLOW}Phase 3: Starting application services${NC}"

# Start application services
docker-compose up -d adhd-support auth-service

echo "Waiting for application services..."
sleep 15

# Check application services
check_service "ADHD Support" "curl -s http://127.0.0.1:8001/health"
check_service "Auth Service" "curl -s http://127.0.0.1:8003/health"

echo ""
echo -e "${BLUE}Service Status:${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}✅ Service startup test completed!${NC}"
echo ""
echo -e "${YELLOW}To stop test services:${NC}"
echo "docker-compose down"
