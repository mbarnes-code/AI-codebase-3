#!/bin/bash
# health-check.sh - Comprehensive health monitoring for AI Second Brain Platform

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_service() {
    local service_name="$1"
    local url="$2"
    local timeout="${3:-5}"
    
    if curl -s --connect-timeout "$timeout" "$url" >/dev/null 2>&1; then
        print_status "$service_name is healthy"
        return 0
    else
        print_error "$service_name is not responding"
        return 1
    fi
}

print_header "🏥 AI Second Brain Platform Health Check"
echo "Timestamp: $(date)"
echo "Hostname: $(hostname)"
echo "IP Address: $(hostname -I | awk '{print $1}')"

# System Resources
print_header "💻 System Resources"

# CPU Usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
echo "CPU Usage: ${CPU_USAGE}%"

# Memory Usage
MEMORY_INFO=$(free -h | grep "Mem:")
TOTAL_MEM=$(echo "$MEMORY_INFO" | awk '{print $2}')
USED_MEM=$(echo "$MEMORY_INFO" | awk '{print $3}')
AVAIL_MEM=$(echo "$MEMORY_INFO" | awk '{print $7}')
echo "Memory: ${USED_MEM}/${TOTAL_MEM} used, ${AVAIL_MEM} available"

# Disk Usage
DISK_INFO=$(df -h / | tail -1)
DISK_USED=$(echo "$DISK_INFO" | awk '{print $5}')
DISK_AVAIL=$(echo "$DISK_INFO" | awk '{print $4}')
echo "Disk: ${DISK_USED} used, ${DISK_AVAIL} available"

# Load Average
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}')
echo "Load Average:${LOAD_AVG}"

# Check if we're hitting CPU constraints (Jane's bottleneck)
CPU_PERCENT=$(echo "$CPU_USAGE" | sed 's/%//')
if (( $(echo "$CPU_PERCENT > 80" | bc -l) )); then
    print_warning "High CPU usage detected (${CPU_PERCENT}%). Consider reducing background tasks."
elif (( $(echo "$CPU_PERCENT > 95" | bc -l) )); then
    print_error "Critical CPU usage (${CPU_PERCENT}%)! Immediate action required."
fi

# Docker Services Health
print_header "🐳 Docker Services"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker daemon is not running"
    exit 1
fi

print_status "Docker daemon is running"

# Get container status
echo
echo "Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(redis|postgres|adhd-support|auth-service|mcp-server|prometheus|grafana)" || echo "No matching containers found"

# Service Health Checks
print_header "🩺 Service Health Checks"

FAILED_SERVICES=0

# Core Infrastructure
echo "Core Infrastructure:"
if ! check_service "Redis" "http://127.0.0.1:6379" 2; then
    ((FAILED_SERVICES++))
fi

if ! check_service "PostgreSQL" "http://127.0.0.1:5432" 2; then
    # Alternative check for PostgreSQL
    if docker-compose exec -T spellbook-db pg_isready -U spellbook_user >/dev/null 2>&1; then
        print_status "PostgreSQL is healthy"
    else
        print_error "PostgreSQL is not responding"
        ((FAILED_SERVICES++))
    fi
fi

# ADHD Support Services (Priority #1)
echo
echo "ADHD Support Services (Priority #1):"
if ! check_service "ADHD Support API" "http://127.0.0.1:8001/health"; then
    ((FAILED_SERVICES++))
fi

if ! check_service "Authentication Service" "http://127.0.0.1:8003/health"; then
    ((FAILED_SERVICES++))
fi

# Development Services
echo
echo "Development Services:"
if ! check_service "MCP Server" "http://127.0.0.1:8002/health"; then
    ((FAILED_SERVICES++))
fi

if ! check_service "Commander Spellbook" "http://127.0.0.1:3001" 10; then
    ((FAILED_SERVICES++))
fi

# Monitoring Services
echo
echo "Monitoring Services:"
if ! check_service "Prometheus" "http://127.0.0.1:9090/-/healthy"; then
    ((FAILED_SERVICES++))
fi

if ! check_service "Grafana" "http://127.0.0.1:3000/api/health"; then
    ((FAILED_SERVICES++))
fi

# External Services
echo
echo "External Services:"
if ! check_service "Motoko LLM Server" "http://192.168.1.12:8000/health" 10; then
    print_warning "Motoko LLM server not accessible. AI features may be limited."
    ((FAILED_SERVICES++))
fi

# Network Connectivity
print_header "🌐 Network Connectivity"

# Check Motoko connectivity
if ping -c 1 192.168.1.12 >/dev/null 2>&1; then
    print_status "Motoko server (192.168.1.12) is reachable"
else
    print_error "Motoko server (192.168.1.12) is not reachable"
fi

# Check internet connectivity
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    print_status "Internet connectivity is available"
else
    print_warning "Internet connectivity may be limited"
fi

# Resource Usage by Container
print_header "📊 Container Resource Usage"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | head -10

# Recent Logs Check
print_header "📝 Recent Error Logs"
echo "Checking for recent errors in service logs..."

# Check for errors in the last 5 minutes
SINCE_TIME=$(date -d '5 minutes ago' '+%Y-%m-%dT%H:%M:%S')

SERVICES=("adhd-support" "auth-service" "mcp-server" "prometheus" "grafana")
for service in "${SERVICES[@]}"; do
    ERROR_COUNT=$(docker-compose logs --since="$SINCE_TIME" "$service" 2>/dev/null | grep -i error | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        print_warning "$service has $ERROR_COUNT errors in the last 5 minutes"
    fi
done

# Database Connection Test
print_header "🗄️ Database Connectivity"

# Test PostgreSQL connection
if docker-compose exec -T spellbook-db psql -U spellbook_user -d spellbook_db -c "SELECT 1;" >/dev/null 2>&1; then
    print_status "PostgreSQL connection test successful"
else
    print_error "PostgreSQL connection test failed"
fi

# Test Redis connection
if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    print_status "Redis connection test successful"
else
    print_error "Redis connection test failed"
fi

# Summary
print_header "📋 Health Check Summary"

TOTAL_CHECKS=$((8 + ${#SERVICES[@]}))  # Adjust based on actual number of checks
SUCCESS_RATE=$(( (TOTAL_CHECKS - FAILED_SERVICES) * 100 / TOTAL_CHECKS ))

echo "Overall Health Score: ${SUCCESS_RATE}%"
echo "Failed Services: ${FAILED_SERVICES}"

if [ "$FAILED_SERVICES" -eq 0 ]; then
    print_status "🎉 All systems are healthy!"
    exit 0
elif [ "$FAILED_SERVICES" -le 2 ]; then
    print_warning "⚠️ Some services are degraded but core functionality is available"
    exit 1
else
    print_error "❌ Multiple services are failing. System requires attention."
    exit 2
fi
