# AI Second Brain Platform

**ADHD/Autism Executive Function Support + Cybersecurity Research Platform**

Multi-service AI system with Jane (Intel NUC service hub) and Motoko (AMD Ryzen AI server), featuring comprehensive ADHD support, code analysis, and cybersecurity tools.

## 🎯 Project Vision

**Primary Goal**: Create an AI "friend" and "second brain" that provides reliable ADHD/autism executive function support while enabling cybersecurity research through unified tool consolidation.

**Key Principles**:
- ADHD support is **Priority #1** - always responsive, sub-second response times
- Resource-aware architecture that respects Jane's CPU constraints  
- Security-first design with proper authentication and secrets management
- Container-first, API-driven architecture for maintainability

## 🏗️ System Architecture

### Jane Server (192.168.1.17) - Service Hub
- **Hardware**: Intel NUC i3-10110U (2C/4T), 64GB RAM, 1.5TB storage
- **Role**: Frontend, API gateway, databases, monitoring, ADHD support
- **Critical Constraint**: Dual-core CPU is the system bottleneck

**Services**:
- 🧠 **ADHD Support API** (Port 8001) - Task management, focus tracking, AI assistance
- 🔐 **Authentication Service** (Port 8003) - JWT, API keys, Vault integration  
- 🔧 **MCP Server** (Port 8002) - Code analysis, security scanning
- 📊 **Monitoring Stack** - Grafana (3000), Prometheus (9090)
- 🗄️ **Data Layer** - PostgreSQL, Redis, Qdrant vector DB
- 🌐 **Web Services** - Commander Spellbook MTG app (3001)

### Motoko Server (192.168.1.12) - AI Brain  
- **Hardware**: AMD Ryzen 9 5900X (12C/24T), 128GB RAM, RTX 3090 (24GB VRAM)
- **Role**: AI inference, heavy computation, context management
- **Services**: Ollama LLM server, FastAPI endpoints

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Both servers need Docker and Docker Compose
sudo apt update && sudo apt install docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```

### 2. Setup Jane (Primary Server)
```bash
# Clone repository
git clone <repository-url>
cd AI-codebase-3

# Generate secrets and environment configuration
./setup-secrets.sh

# Edit .env with your actual values
nano .env

# Start all services (with resource-aware scheduling)
./startup.sh
```

### 3. Setup Motoko (AI Server)
```bash
# Start LLM service on Motoko
cd /path/to/motoko/llm
./start_server.sh
```

### 4. Verify Installation
```bash
# Comprehensive health check
./health-check.sh

# Full integration test
./integration_test.sh
```

## 🧠 ADHD Support Features (Priority #1)

### Task Management with Executive Function Support
```bash
# Create a task with ADHD-friendly structure
curl -X POST http://127.0.0.1:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Review security analysis results", 
    "priority": 4,
    "estimated_duration": 30,
    "context": "work",
    "tags": ["security", "urgent"]
  }'

# Get tasks filtered by context
curl "http://127.0.0.1:8001/tasks?context=work&completed=false"
```

### Focus Sessions (Pomodoro-style)
```bash
# Start a focus session
curl -X POST http://127.0.0.1:8001/focus-sessions \
  -H "Content-Type: application/json" \
  -d '{
    "duration_minutes": 25,
    "break_duration": 5,
    "task_id": "uuid-of-task"
  }'

# Check active sessions
curl http://127.0.0.1:8001/focus-sessions/active
```

### AI-Powered Executive Function Assistance
```bash
# Get ADHD-optimized AI assistance
curl -X POST http://127.0.0.1:8001/ai/ask \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Help me break down this complex cybersecurity audit into manageable steps",
    "context": "work",
    "conversation_id": "session-123"
  }'
```

### Quick Notes & Brain Dumps
```bash
# Capture thoughts quickly (essential for ADHD)
curl -X POST http://127.0.0.1:8001/notes \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Remember to check the new vulnerability scanner results",
    "tags": ["reminder", "security"],
    "context": "work"
  }'
```

## 🔧 Code Analysis & Cybersecurity Tools

### MCP Server - Model Context Protocol
Advanced code analysis with security focus:

```bash
# Comprehensive codebase analysis
curl -X POST http://127.0.0.1:8002/analyze/codebase \
  -H "Content-Type: application/json" \
  -d '{
    "repository_path": "/path/to/target/repo",
    "language": "python", 
    "analysis_type": "security",
    "target_language": "go"
  }'

# Focused security analysis
curl -X POST http://127.0.0.1:8002/analyze/security \
  -H "Content-Type: application/json" \
  -d '{
    "code_path": "/path/to/code",
    "scan_types": ["static", "dependency", "secrets"]
  }'
```

**Analysis Capabilities**:
- Static analysis with Semgrep, Bandit, Gosec
- Dependency vulnerability scanning with Trivy
- Code structure and complexity analysis
- Conversion feasibility assessment
- AI-powered recommendations

## 🔐 Security & Authentication

### JWT Authentication
```bash
# Register new user
curl -X POST http://127.0.0.1:8003/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "researcher",
    "email": "user@example.com", 
    "password": "SecurePass123!",
    "full_name": "Security Researcher"
  }'

# Login and get token
curl -X POST http://127.0.0.1:8003/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "researcher",
    "password": "SecurePass123!"
  }'
```

### API Key Management
```bash
# Create API key for service authentication
curl -X POST http://127.0.0.1:8003/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MCP Server Access",
    "permissions": ["analysis:read", "analysis:write"],
    "expires_days": 90
  }'
```

## 📊 Monitoring & Observability

### Grafana Dashboards
- **ADHD Support Dashboard**: Task completion rates, focus session analytics
- **System Health**: CPU (critical for Jane), memory, disk usage
- **Security Dashboard**: Failed logins, vulnerability scan results
- **Performance**: API response times, service uptime

### Key Metrics for ADHD Platform
- **Response Time**: ADHD support APIs must be <1 second
- **Task Completion**: Daily/weekly completion rates
- **Focus Session Success**: Session completion and break adherence
- **AI Interaction**: Usage patterns and response quality

### Access Points
- **Grafana**: http://127.0.0.1:3000 (admin/admin123)
- **Prometheus**: http://127.0.0.1:9090  
- **API Documentation**: Each service has `/docs` endpoint

## ⚡ Resource Management (Critical)

### Jane CPU Constraints
```bash
# Monitor CPU usage (critical bottleneck)
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# ADHD services resource allocation
ADHD Support:    <20% CPU (always priority)
Authentication:  <10% CPU  
Core DBs:        <15% CPU
Monitoring:      <10% CPU
Background:      Remaining capacity
```

### Intelligent Service Scheduling
- **Always Priority**: ADHD support services
- **Peak Hours**: Disable heavy analysis containers
- **Off-Peak**: Schedule security scans, updates
- **Resource Alerts**: CPU >80% triggers service scaling

## 🛡️ Cybersecurity Research Integration

### Tool Consolidation Strategy
**Phase 1 - Go Ecosystem** (High Priority):
- Nuclei, Amass, Subfinder, Httpx, Gobuster  
- Target: Unified reconnaissance platform

**Phase 2 - Python Ecosystem** (Medium Priority):
- SQLMap, Volatility, YARA
- Target: Analysis framework integration

**Phase 3 - Performance Critical** (Integration Only):
- Suricata, Zeek, Masscan
- Target: API integration while preserving performance

### MCP Tools Available
```bash
# List available analysis tools
curl http://127.0.0.1:8002/tools

# Available tools:
# - codebase_scan: Repository analysis
# - security_scan: Vulnerability assessment  
# - conversion_assess: Code conversion evaluation
# - pattern_learn: Security pattern recognition
```

## 🔄 Development Workflow

### Container-First Development
```bash
# Build and test locally
docker-compose build service-name
docker-compose up -d service-name
docker-compose logs -f service-name

# Resource-aware deployment
docker-compose up -d --scale mcp-server=0  # Peak hours
docker-compose up -d --scale mcp-server=1  # Off-peak
```

### API-First Integration
- All services expose OpenAPI/Swagger documentation
- Consistent error handling and response formats
- Rate limiting to protect Jane's CPU resources
- Health checks for monitoring integration

## 🧪 Testing & Validation

### Comprehensive Test Suite
```bash
# Quick health check
./health-check.sh

# Full integration test  
./integration_test.sh

# Performance validation
./performance-test.sh  # (to be created)
```

### Critical Test Categories
1. **ADHD Support Responsiveness**: <1s response time
2. **Jane-Motoko Communication**: AI request flow
3. **Resource Constraints**: CPU usage under limits
4. **Security**: Authentication and authorization
5. **Data Persistence**: Task and session storage

## 📋 Troubleshooting

### Common Issues

#### High CPU Usage (Jane)
```bash
# Identify CPU-heavy containers
docker stats

# Scale down non-critical services
docker-compose stop mcp-server n8n

# Monitor ADHD support responsiveness
curl -w "%{time_total}" http://127.0.0.1:8001/health
```

#### Service Not Responding
```bash
# Check container health
docker-compose ps

# View detailed logs
docker-compose logs --tail=50 service-name

# Restart individual service
docker-compose restart service-name
```

#### Motoko Connection Issues
```bash
# Test network connectivity
ping 192.168.1.12

# Check LLM service
curl http://192.168.1.12:8000/health

# Restart Motoko service (from Motoko server)
./motoko/llm/start_server.sh
```

### Emergency Procedures
1. **ADHD Support Down**: Immediate priority - restart ADHD services
2. **High CPU**: Scale down analysis services, prioritize core functions
3. **Database Issues**: Check logs, verify connections, restart if needed
4. **AI Features Down**: Verify Motoko connectivity, check model availability

## 🎯 Success Metrics

### Primary (ADHD Support)
- **Daily Task Creation**: User engagement indicator
- **Focus Session Completion**: Executive function improvement
- **AI Interaction Quality**: User satisfaction with assistance
- **Response Time**: <1 second for all ADHD support APIs

### Secondary (Technical)
- **System Uptime**: >99% availability for core services
- **Resource Efficiency**: Jane CPU <80% average
- **Security**: Zero authentication bypasses
- **Code Analysis**: Successful vulnerability detection

### Long-term (Research)
- **Tool Consolidation**: Reduced complexity, unified workflows
- **Pattern Learning**: Improved AI recommendations over time
- **User Adaptation**: System learns user preferences and patterns

---

## 📚 Additional Documentation

- **[Setup Guide](SETUP_GUIDE.md)**: Detailed installation instructions
- **[Project Specification](PROJECT_SPECIFICATION.md)**: Complete technical specification
- **[Integration Status](INTEGRATION_STATUS.md)**: Current implementation status
- **[Security Guide](SECURITY.md)**: Security configuration and best practices

## 🆘 Support & Maintenance

**Remember**: This system is designed for a user with ADHD. Priority #1 is always keeping the executive function support responsive and reliable. When in doubt, ensure ADHD support services are running smoothly before addressing other issues.

For questions, issues, or contributions, please refer to the troubleshooting section or check the service logs for detailed error information.

## 🚀 Quick Start

### Start All Services
```bash
# Start Jane services
docker-compose up -d

# Start Motoko LLM server
cd motoko/llm
docker-compose up -d
```

### Access Points
- **Dashboard**: http://192.168.1.17:3002
- **Commander Spellbook**: http://192.168.1.17:3001
- **Django Admin**: http://192.168.1.17:8000/admin
- **Grafana**: http://192.168.1.17:3000
- **Motoko LLM API**: http://192.168.1.12:8000/docs

## 🔒 Security Features

- Docker secrets management
- Environment variable configuration
- API key authentication
- Rate limiting and input validation
- Secure container deployment
- Authentication required for dashboard access

## 📁 Project Structure

```
/
├── Jane/
│   ├── dashboard/              # Service monitoring dashboard
│   ├── commander-spellbook-*/  # MTG combo database
│   └── ai-workflow-fastapi/    # AI workflow service
├── motoko/
│   └── llm/                    # LLM inference server
├── secrets/                    # Secure configuration files
├── docker-compose.yml          # Main service orchestration
├── .env.template              # Environment template
├── SECURITY.md                # Security documentation
└── DEBUG_REPORT.md            # System status report
```

## 🛠️ Development

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for dashboard development)
- Python 3.11+ (for LLM server development)

### Dashboard Development
```bash
cd Jane/dashboard
npm install
npm run dev
```

### LLM Server Development
```bash
cd motoko/llm
pip install -r requirements.txt
uvicorn llm_server:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Monitoring

The system includes comprehensive monitoring via:
- **Jane Dashboard**: Real-time service health and metrics
- **Grafana**: Advanced metrics visualization
- **Prometheus**: Metrics collection and alerting
- **Health Endpoints**: Standardized health checks across all services

## 🔄 Deployment

### Production Deployment
```bash
# Configure environment
cp .env.template .env
# Edit .env with production values

# Deploy Jane services
docker-compose -f docker-compose.yml up -d

# Deploy Motoko services
cd motoko && docker-compose up -d
```

### Security Checklist
- [ ] Update default passwords
- [ ] Configure API keys
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Enable monitoring alerts

## 📚 Documentation

- [Security Guide](SECURITY.md)
- [Debug Report](DEBUG_REPORT.md)
- [Dashboard README](Jane/dashboard/README.md)
- [Integration Status](INTEGRATION_STATUS.md)

## 🚀 Latest Updates

✅ **Completed Dashboard Implementation**
- Full Grafana-style UI with dark theme
- Real-time health monitoring for all services
- Authentication and auto-refresh functionality
- Responsive design with service navigation
- Production-ready deployment

✅ **Security Hardening**
- Docker secrets implementation
- Container security best practices
- API authentication and rate limiting
- Environment variable management

✅ **Service Integration**
- Cross-server communication setup
- Standardized health check endpoints
- Centralized monitoring and logging
- Docker orchestration optimization

---

**System Status**: ✅ Production Ready
**Dashboard**: http://192.168.1.17:3002 (admin@jane.local / admin123)
**Primary AI**: http://192.168.1.12:8000