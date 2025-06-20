# LLM Installation & Configuration for Motoko

This folder contains all scripts, requirements, and configuration files needed to install and run LLMs (Large Language Models) on the Motoko server.

## How to Use

### 1. Build and Run the LLM Server

```bash
cd motoko/llm
# Build Docker image
sudo docker build -t motoko-llm .
# Run the server (expose to local network)
sudo docker run -p 8000:8000 --gpus all --env-file .env motoko-llm
```

The FastAPI server will be available at `http://<motoko-ip>:8000`.

### 2. API Usage (from Jane or other clients)

- **POST /generate**
  - Request body: `{ "prompt": "your prompt", "model": "llama2" }`
  - Response: `{ "response": "..." }`

- **GET /health**
  - Returns `{ "status": "ok" }`

### 3. Example Python Client (from Jane)

```python
import requests
resp = requests.post(
    "http://<motoko-ip>:8000/generate",
    json={"prompt": "Hello, world!", "model": "llama2"}
)
print(resp.json())
```

## Example Structure
- `requirements.txt` — Python dependencies for LLMs
- `Dockerfile` — Container setup for LLM services
- `llm_server.py` — FastAPI LLM server
- `README.md` — This file

## Notes
- Keep all LLM-specific configuration here to keep the project organized and maintainable.
- If you add new LLMs or change the setup, update this README and related files.
