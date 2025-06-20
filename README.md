# AI-codebase-3

Multi-service AI system with Jane (service hub) and Motoko (LLM backend) servers, featuring a centralized monitoring dashboard.

## 🚀 System Overview

### Jane Server (192.168.1.17)
- **Role**: Service hub, databases, monitoring, APIs
- **OS**: Ubuntu LTS 24.04
- **Hardware**: Intel NUC i3-10110U, 64GB RAM, 512GB SSD + 1TB NVMe
- **Services**: Qdrant, Redis, N8N, PostgreSQL, Nginx, Django, Next.js, Grafana, Prometheus, Apache Tika, XTTS, MCP Server, Scrape4AI

### Motoko Server (192.168.1.12)
- **Role**: Central AI brain for all processing
- **OS**: Ubuntu LTS 24.04
- **Hardware**: AMD Ryzen 9 5900X, 128GB RAM, RTX 3090 (24GB VRAM), 8TB NVMe
- **Services**: Ollama, FastAPI LLM server

## 🔧 Components

### 1. Jane Dashboard (Port 3002)
Centralized Grafana-style monitoring dashboard for all services.

**Features:**
- Real-time health checks and metrics
- Authentication required (admin@jane.local / admin123)
- Auto-refresh with configurable intervals
- Direct navigation to service interfaces
- Responsive design with dark theme

**Access:** http://192.168.1.17:3002

### 2. Commander Spellbook (Ports 3001, 8000)
Magic: The Gathering combo database and deck builder.

**Components:**
- Next.js frontend (Port 3001)
- Django REST API backend (Port 8000)
- PostgreSQL database
- AI-powered deck building integration

### 3. Motoko LLM Server (Port 8000)
FastAPI-based AI inference server with security features.

**Features:**
- API key authentication
- Rate limiting and input validation
- Health monitoring endpoints
- Docker deployment ready

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