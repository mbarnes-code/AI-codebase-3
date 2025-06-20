# Jane Service Dashboard

A centralized monitoring dashboard for all Jane services with real-time health checks and metrics.

## Features

- **Real-time Monitoring**: Live health checks for all services
- **Detailed Metrics**: CPU, memory, response times, and service status
- **Grafana-style UI**: Professional monitoring interface
- **Authentication**: Secure access with login required
- **Auto-refresh**: Configurable refresh intervals
- **Service Navigation**: Direct links to service interfaces
- **External Monitoring**: Health checks for Motoko server

## Services Monitored

### Jane Services
- Qdrant (Vector Database)
- Redis (Cache/Session Store)
- N8N (Workflow Automation)
- Apache Tika (Document Processing)
- PostgreSQL (Database)
- Nginx (Web Server)
- XTTS (Text-to-Speech)
- MCP Server (Model Context Protocol)
- Django Backend
- FastAPI Services
- Grafana/Prometheus (Monitoring)
- Scrape4AI (Web Scraping)

### External Services
- Motoko LLM Server (192.168.1.12:8000)
- Ollama Service (via Motoko)

## Installation

```bash
cd Jane/dashboard
npm install
npm run dev
```

## Configuration

Environment variables in `.env.local`:
```
NEXTAUTH_SECRET=your-secret-key
NEXTAUTH_URL=http://192.168.1.17:3002
DASHBOARD_AUTH_ENABLED=true
```

## Usage

1. Navigate to `http://192.168.1.17:3002`
2. Login with credentials
3. Monitor service status and metrics
4. Click service cards to navigate to interfaces
5. Use refresh controls for manual updates

## Security

- Authentication required for access
- Rate limiting on API endpoints
- Secure port configuration (3002)
- Input validation and sanitization
