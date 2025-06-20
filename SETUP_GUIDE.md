# 🚀 AI Second Brain Platform - Quick Start Guide

## Overview

The AI Second Brain Platform is a comprehensive ADHD/autism executive function support system with cybersecurity research capabilities. It runs on a distributed architecture with Jane (Intel NUC) as the service hub and Motoko (AMD Ryzen + RTX 3090) as the AI brain.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Jane (192.168.1.17) - Intel NUC i3-10110U, 64GB RAM             │
├─────────────────────────────────────────────────────────────────┤
│ 🧠 ADHD Support (Priority #1)                                   │
│ • Task Management & Focus Sessions                               │
│ • AI-Powered Executive Function Support                         │
│ • Real-time Chat Interface                                      │
│                                                                 │
│ 🔐 Core Infrastructure                                          │
│ • Authentication & Authorization                                │
│ • PostgreSQL Database                                           │
│ • Redis Cache                                                   │
│ • Monitoring & Observability                                    │
│                                                                 │
│ 🔧 Development Tools                                            │
│ • MCP Server (Code Analysis)                                    │
│ • Commander Spellbook (MTG)                                     │
│ • Security Analysis Tools                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Motoko (192.168.1.12) - AMD Ryzen 9 5900X, RTX 3090            │
├─────────────────────────────────────────────────────────────────┤
│ 🤖 AI Inference Engine                                          │
│ • Ollama LLM Server                                             │
│ • Context Management                                            │
│ • Heavy Computation Tasks                                       │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- **Jane Server**: Ubuntu 24.04 LTS, Docker, Docker Compose
- **Motoko Server**: Ubuntu 24.04 LTS with Ollama installed
- **Network**: Both servers on same network (192.168.1.x)

### 2. Setup Jane (Service Hub)

```bash
# Clone the repository
git clone <repository-url>
cd AI-codebase-3

# Generate secrets and environment
./setup-secrets.sh

# Edit .env with your actual values
nano .env

# Start all services
./startup.sh
```

### 3. Setup Motoko (AI Server)

```bash
# On Motoko server, start LLM service
cd /workspaces/AI-codebase-3/motoko/llm
./start_server.sh
```

### 4. Verify Installation

```bash
# Run health check
./health-check.sh

# Test integration
./integration_test.sh
```

## 🎯 Core Services

### ADHD Support Stack (Priority #1)
- **URL**: http://127.0.0.1:8001/docs
- **Purpose**: Task management, focus sessions, AI assistance
- **Resource Allocation**: <20% CPU, always responsive

### Authentication & Security
- **URL**: http://127.0.0.1:8003/docs
- **Purpose**: JWT authentication, API keys, Vault integration

### Code Analysis (MCP Server)
- **URL**: http://127.0.0.1:8002/docs
- **Purpose**: Security scanning, code conversion, vulnerability assessment

### Monitoring Dashboard
- **Grafana**: http://127.0.0.1:3000 (admin/admin123)
- **Prometheus**: http://127.0.0.1:9090

## 📊 Resource Management

### Jane CPU Constraints (Critical)
- **Total CPU**: 2 cores (i3-10110U) - BOTTLENECK
- **ADHD Support**: Always priority, <20% CPU reserved
- **Background Tasks**: Scheduled during off-peak hours
- **Heavy Analysis**: Offloaded to Motoko or containerized

### Memory Allocation
- **Available**: 64GB (abundant)
- **Core Services**: ~8GB
- **Analysis Containers**: 25GB burst capacity
- **Monitoring**: 4GB

### Storage Strategy
- **Hot Data**: NVMe SSD (512GB + 1TB)
- **Cold Data**: NAS storage
- **Container Images**: Local cache with cleanup

## 🛡️ Security Configuration

### Network Security
- **VPN**: Tailscale/WireGuard for device communication
- **Firewall**: UFW with restrictive rules
- **SSL/TLS**: Automated certificates via Let's Encrypt

### Secrets Management
- **Vault**: HashiCorp Vault for secret storage
- **Environment**: No hardcoded secrets in code
- **Rotation**: Automated secret rotation policies

### Authentication
- **JWT**: Bearer token authentication
- **API Keys**: Service-to-service communication
- **RBAC**: Role-based access control

## 🧠 ADHD Support Features

### Task Management
```bash
# Create a task
curl -X POST http://127.0.0.1:8001/tasks \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Review code changes",
    "priority": 4,
    "estimated_duration": 30,
    "context": "work"
  }'
```

### Focus Sessions
```bash
# Start a focus session
curl -X POST http://127.0.0.1:8001/focus-sessions \\
  -H "Content-Type: application/json" \\
  -d '{
    "duration_minutes": 25,
    "break_duration": 5
  }'
```

### AI Assistance
```bash
# Ask AI for help
curl -X POST http://127.0.0.1:8001/ai/ask \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Help me break down this complex task into smaller steps",
    "context": "work"
  }'
```

## 🔧 Development Workflow

### Code Analysis
```bash
# Analyze a codebase
curl -X POST http://127.0.0.1:8002/analyze/codebase \\
  -H "Content-Type: application/json" \\
  -d '{
    "repository_path": "/path/to/repo",
    "language": "python",
    "analysis_type": "security"
  }'
```

### Security Scanning
```bash
# Run security scan
curl -X POST http://127.0.0.1:8002/analyze/security \\
  -H "Content-Type: application/json" \\
  -d '{
    "code_path": "/path/to/code",
    "scan_types": ["static", "dependency", "secrets"]
  }'
```

## 📈 Monitoring & Alerting

### Key Metrics
- **CPU Usage**: Critical for Jane's dual-core constraint
- **Response Time**: ADHD support must be <1s
- **Service Health**: All core services monitored
- **Resource Usage**: Container-level monitoring

### Alert Channels
- **Grafana**: Visual dashboards and alerts
- **Prometheus**: Metric collection and rules
- **Health Check**: Automated status monitoring

### Custom Dashboards
- **ADHD Support**: Task completion, focus sessions
- **System Health**: CPU, memory, disk usage
- **Security**: Failed logins, vulnerability scans

## 🐛 Troubleshooting

### Common Issues

#### Service Not Responding
```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs [service-name]

# Restart service
docker-compose restart [service-name]
```

#### High CPU Usage (Jane)
```bash
# Check container resource usage
docker stats

# Scale down non-critical services
docker-compose stop mcp-server

# Run analysis during off-peak hours
```

#### Motoko Connection Issues
```bash
# Test network connectivity
ping 192.168.1.12

# Check Motoko service
curl http://192.168.1.12:8000/health

# Restart Motoko service
ssh motoko "cd /path/to/llm && ./start_server.sh"
```

### Log Locations
- **Service Logs**: `docker-compose logs [service]`
- **Application Logs**: `/app/logs/` in containers
- **System Logs**: `/var/log/syslog`

### Performance Optimization
- **CPU**: Adjust container resource limits
- **Memory**: Enable swap if needed
- **Disk**: Use SSD for databases, regular cleanup
- **Network**: Optimize service communication

## 🔄 Maintenance

### Daily
- **Health Check**: `./health-check.sh`
- **Resource Monitor**: Check Grafana dashboards
- **Backup Status**: Verify automated backups

### Weekly
- **Update Check**: Security updates for containers
- **Log Rotation**: Clean old log files
- **Performance Review**: Analyze resource trends

### Monthly
- **Security Audit**: Review access logs and permissions
- **Capacity Planning**: Assess storage and compute needs
- **Configuration Review**: Update settings as needed

## 📚 API Documentation

### ADHD Support API
- **Interactive Docs**: http://127.0.0.1:8001/docs
- **OpenAPI Spec**: http://127.0.0.1:8001/openapi.json

### Authentication API
- **Interactive Docs**: http://127.0.0.1:8003/docs
- **OpenAPI Spec**: http://127.0.0.1:8003/openapi.json

### MCP Server API
- **Interactive Docs**: http://127.0.0.1:8002/docs
- **OpenAPI Spec**: http://127.0.0.1:8002/openapi.json

## 🆘 Support

### Self-Service
1. **Health Check**: `./health-check.sh`
2. **Logs**: `docker-compose logs [service]`
3. **Documentation**: API docs at `/docs` endpoints
4. **Monitoring**: Grafana dashboards

### Emergency Procedures
1. **System Down**: Run `./startup.sh`
2. **High CPU**: Stop non-critical services
3. **Database Issues**: Check PostgreSQL logs
4. **Network Issues**: Verify Jane-Motoko connectivity

---

**Remember**: ADHD support is Priority #1. If CPU resources are constrained, always ensure ADHD support services remain responsive by reducing other workloads.
