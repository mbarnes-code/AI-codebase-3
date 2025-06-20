# LLM Installation & Configuration for Motoko

This folder contains all scripts, requirements, and configuration files needed to install and run LLMs (Large Language Models) on the Motoko server (192.168.1.12).

## Network Setup

- **Motoko Server**: 192.168.1.12:8000 (this server)
- **Jane Server**: 192.168.1.17:3001 (frontend that connects to this server)

## How to Use

### 1. Build and Run the LLM Server

```bash
cd motoko/llm

# Option 1: Run with Docker
./start_server.sh docker

# Option 2: Run directly with Python
pip install -r requirements.txt
./start_server.sh

# Option 3: Manual Python run
python llm_server.py
```

The FastAPI server will be available at `http://192.168.1.12:8000`.

### 2. API Endpoints

- **POST /generate**
  - Request body: `{ "prompt": "your prompt", "model": "llama2", "options": {} }`
  - Response: `{ "response": "..." }`

- **GET /health**
  - Returns `{ "status": "ok" }`

### 3. Testing from Jane Server

From Jane (192.168.1.17), you can test connectivity:

```bash
# Test health endpoint
curl http://192.168.1.12:8000/health

# Test generate endpoint
curl -X POST http://192.168.1.12:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!", "model": "llama2"}'
```

### 4. Jane Integration

Jane's API endpoint (`/api/ai/build-deck`) automatically connects to this server using the environment variable `NEXT_PUBLIC_LLM_SERVER_URL=http://192.168.1.12:8000`.

You can check connectivity from Jane by visiting: `http://192.168.1.17:3001/api/ai/health`

## Files Structure

- `requirements.txt` — Python dependencies for LLMs
- `Dockerfile` — Container setup for LLM services  
- `llm_server.py` — FastAPI LLM server with CORS support
- `start_server.sh` — Convenience script to start the server
- `README.md` — This file

## Troubleshooting

1. **Connection refused**: Ensure the server is running and listening on 0.0.0.0:8000
2. **CORS errors**: Check that Jane's IP (192.168.1.17) is in the allowed origins
3. **Network issues**: Verify both servers can ping each other on the network

## Notes

- The server listens on all interfaces (0.0.0.0) to accept connections from Jane
- CORS is configured to allow requests from Jane's IP address
- All LLM-specific configuration should be kept in this folder for organization
