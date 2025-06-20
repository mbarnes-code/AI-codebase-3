#!/bin/bash
# startup.sh - Complete startup script for AI Second Brain Platform

set -euo pipefail

echo "🚀 Starting AI Second Brain Platform..."
echo "========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "\n${BLUE}[STEP]${NC} $1"
}

# Check if running on Jane
if [ "$(hostname -I | grep -c '192.168.1.17')" -eq 0 ]; then
    print_warning "This script is designed to run on Jane (192.168.1.17)"
    print_warning "Current IP: $(hostname -I)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check prerequisites
print_step "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    print_step "Setting up environment configuration..."
    if [ -f ".env.template" ]; then
        cp .env.template .env
        print_warning "Created .env from template. Please edit .env with your actual values."
        print_warning "Run './setup-secrets.sh' to generate secrets."
        echo "Press Enter when you've configured .env..."
        read
    else
        print_error ".env.template not found. Cannot create .env file."
        exit 1
    fi
fi

# Setup secrets if they don't exist
if [ ! -d "secrets" ] || [ ! -f "secrets/postgres_password.txt" ]; then
    print_step "Setting up secrets..."
    if [ -f "./setup-secrets.sh" ]; then
        ./setup-secrets.sh
    else
        print_error "setup-secrets.sh not found. Cannot generate secrets."
        exit 1
    fi
fi

print_status "Prerequisites check completed"

# Check Motoko connectivity
print_step "Checking Motoko server connectivity..."
MOTOKO_IP="192.168.1.12"
if ping -c 1 "$MOTOKO_IP" &> /dev/null; then
    print_status "Motoko server ($MOTOKO_IP) is reachable"
    
    # Check if Motoko LLM service is running
    if curl -s --connect-timeout 5 "http://$MOTOKO_IP:8000/health" &> /dev/null; then
        print_status "Motoko LLM service is running"
    else
        print_warning "Motoko LLM service is not responding. Starting it may be needed."
    fi
else
    print_warning "Motoko server ($MOTOKO_IP) is not reachable"
    print_warning "Jane-Motoko communication may not work properly"
fi

# Check available resources
print_step "Checking system resources..."

# Check CPU cores (Jane constraint)
CPU_CORES=$(nproc)
print_status "Available CPU cores: $CPU_CORES"
if [ "$CPU_CORES" -le 2 ]; then
    print_warning "Limited CPU cores detected. Resource-aware scheduling is critical."
fi

# Check available memory
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
AVAIL_MEM=$(free -g | awk '/^Mem:/{print $7}')
print_status "Total memory: ${TOTAL_MEM}GB, Available: ${AVAIL_MEM}GB"

# Check disk space
DISK_USAGE=$(df -h . | awk 'NR==2{print $5}' | sed 's/%//')
print_status "Disk usage: ${DISK_USAGE}%"
if [ "$DISK_USAGE" -gt 85 ]; then
    print_warning "Disk usage is high (${DISK_USAGE}%). Monitor storage carefully."
fi

# Stop existing containers
print_step "Stopping existing containers..."
docker-compose down --remove-orphans || true

# Pull/build images
print_step "Building and pulling container images..."
docker-compose build --parallel
docker-compose pull

# Start core infrastructure first
print_step "Starting core infrastructure..."
print_status "Starting databases and cache..."
docker-compose up -d redis spellbook-db vault

# Wait for databases to be ready
print_status "Waiting for databases to initialize..."
sleep 10

# Check database health
print_status "Checking database connectivity..."
for i in {1..30}; do
    if docker-compose exec -T spellbook-db pg_isready -U spellbook_user &> /dev/null; then
        print_status "PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "PostgreSQL failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

for i in {1..30}; do
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        print_status "Redis is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Redis failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Start monitoring stack
print_step "Starting monitoring stack..."
docker-compose up -d prometheus grafana node-exporter

# Start authentication service
print_step "Starting authentication service..."
docker-compose up -d auth-service

# Start ADHD support service (Priority #1)
print_step "Starting ADHD support service (Priority #1)..."
docker-compose up -d adhd-support

# Wait for ADHD service to be ready
print_status "Waiting for ADHD support service..."
for i in {1..60}; do
    if curl -s --connect-timeout 2 "http://127.0.0.1:8001/health" &> /dev/null; then
        print_status "ADHD support service is ready"
        break
    fi
    if [ $i -eq 60 ]; then
        print_warning "ADHD support service taking longer than expected"
        break
    fi
    sleep 1
done

# Start remaining services
print_step "Starting remaining services..."
docker-compose up -d mcp-server qdrant n8n

# Start web services
print_step "Starting web services..."
docker-compose up -d spellbook-backend spellbook-site

# Final health check
print_step "Performing final health checks..."
sleep 5

# Define services and their health check URLs
declare -A services=(
    ["ADHD Support"]="http://127.0.0.1:8001/health"
    ["MCP Server"]="http://127.0.0.1:8002/health"
    ["Auth Service"]="http://127.0.0.1:8003/health"
    ["Prometheus"]="http://127.0.0.1:9090/-/healthy"
    ["Grafana"]="http://127.0.0.1:3000/api/health"
    ["Commander Spellbook"]="http://127.0.0.1:3001"
)

print_status "Health check results:"
for service in "${!services[@]}"; do
    url="${services[$service]}"
    if curl -s --connect-timeout 5 "$url" &> /dev/null; then
        print_status "✅ $service: Healthy"
    else
        print_warning "❌ $service: Not responding"
    fi
done

# Display service URLs
print_step "Service URLs and Access Information"
echo "================================================="
echo
echo -e "${GREEN}🧠 ADHD Support Services (Priority #1):${NC}"
echo "  • ADHD Support API: http://127.0.0.1:8001/docs"
echo "  • Authentication: http://127.0.0.1:8003/docs"
echo
echo -e "${BLUE}🔧 Development & Analysis:${NC}"
echo "  • MCP Server: http://127.0.0.1:8002/docs"
echo "  • Commander Spellbook: http://127.0.0.1:3001"
echo "  • Backend API: http://127.0.0.1:8000/admin"
echo
echo -e "${YELLOW}📊 Monitoring & Observability:${NC}"
echo "  • Grafana: http://127.0.0.1:3000 (admin/admin123)"
echo "  • Prometheus: http://127.0.0.1:9090"
echo "  • Node Exporter: http://127.0.0.1:9100"
echo
echo -e "${BLUE}🔐 Infrastructure:${NC}"
echo "  • Vault: http://127.0.0.1:8200 (dev-token-change-me)"
echo "  • N8N Workflows: http://127.0.0.1:5678"
echo "  • Qdrant Vector DB: http://127.0.0.1:6333"
echo
echo -e "${GREEN}🤖 AI Services:${NC}"
echo "  • Motoko LLM: http://192.168.1.12:8000 (if running)"
echo

# Resource usage summary
print_step "Resource Usage Summary"
echo "========================"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -10

echo
print_status "🎉 AI Second Brain Platform startup completed!"
print_status "ADHD support services are prioritized and should be fully responsive."
print_status "Monitor resource usage and adjust container limits as needed."

# Show next steps
echo
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Open Grafana (http://127.0.0.1:3000) to monitor system health"
echo "2. Test ADHD support API at http://127.0.0.1:8001/docs"
echo "3. Configure authentication and create user accounts"
echo "4. Start Motoko LLM service if not already running"
echo "5. Review logs: docker-compose logs -f [service-name]"
echo
echo "To stop all services: docker-compose down"
echo "To view logs: docker-compose logs -f"
echo "To restart a service: docker-compose restart [service-name]"
