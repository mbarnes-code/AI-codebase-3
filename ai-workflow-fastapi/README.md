# AI Workflow FastAPI Application

A FastAPI application with Ollama, Qdrant, and Redis integration.

## Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd <your-repo-name>
```

### 2. Create Environment File
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python main.py
```

The API will be available at `http://localhost:8001`

## Docker Usage

### Build and Run
```bash
docker build -t ai-workflow-api .
docker run -p 8001:8001 ai-workflow-api
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/status` - API status (rate limited)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_HOST` | Redis server host | `localhost` |
| `REDIS_PORT` | Redis server port | `6379` |
| `REDIS_PASSWORD` | Redis password | `` |

## Development

The application includes:
- **FastAPI** - Modern web framework
- **Rate limiting** - Using slowapi
- **CORS** - Cross-origin resource sharing
- **Health checks** - Built-in monitoring
- **Logging** - Structured logging with loguru
- **Redis** - Caching and state management

## License

MIT License