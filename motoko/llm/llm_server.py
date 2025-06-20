from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import os
import ollama
import secrets
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Motoko LLM Server", 
    description="LLM inference server for Jane frontend",
    docs_url=None,  # Disable docs in production
    redoc_url=None  # Disable redoc in production
)

# Security: API Key authentication
security = HTTPBearer()
API_KEY = os.getenv("LLM_API_KEY", "")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify API key for authentication"""
    if not API_KEY:
        return True  # Skip auth if no key set (development mode)
    
    if not secrets.compare_digest(credentials.credentials, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return True

# Restrictive CORS - only allow specific Jane server IPs
ALLOWED_ORIGINS = [
    "http://192.168.1.17:3001",  # Jane production
    "http://192.168.1.17:3000",  # Jane dev
]

# Only add localhost in development
if os.getenv("ENVIRONMENT", "production") == "development":
    ALLOWED_ORIGINS.extend([
        "http://localhost:3000",
        "http://localhost:3001"
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # More secure
    allow_methods=["POST", "GET"],  # Only specific methods
    allow_headers=["Content-Type", "Authorization"],  # Only required headers
)

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "llama2"
    options: dict = {}
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError('Prompt cannot be empty')
        if len(v) > 8000:  # Reasonable limit
            raise ValueError('Prompt too long (max 8000 characters)')
        return v.strip()
    
    @validator('model')
    def validate_model(cls, v):
        allowed_models = ['llama2', 'mistral', 'codellama', 'llama3']
        if v not in allowed_models:
            raise ValueError(f'Model must be one of: {allowed_models}')
        return v

class GenerateResponse(BaseModel):
    response: str
    model_used: str
    tokens_generated: Optional[int] = None

@app.post("/generate", response_model=GenerateResponse)
def generate_text(req: GenerateRequest, authenticated: bool = Depends(verify_api_key)):
    try:
        logger.info(f"Received generate request for model: {req.model}")
        logger.info(f"Prompt length: {len(req.prompt)} characters")
        
        # Security: Limit options to safe parameters
        safe_options = {
            "temperature": req.options.get("temperature", 0.7),
            "top_p": req.options.get("top_p", 0.9),
            "max_tokens": min(req.options.get("max_tokens", 1000), 2000)  # Cap at 2000
        }
        
        # Call Ollama API (assumes Ollama is running locally or in Docker)
        result = ollama.generate(model=req.model, prompt=req.prompt, options=safe_options)
        
        logger.info("Successfully generated response from Ollama")
        return {
            "response": result["response"],
            "model_used": req.model,
            "tokens_generated": result.get("eval_count")
        }
    except ollama.ResponseError as e:
        logger.error(f"Ollama API error: {e}")
        raise HTTPException(status_code=502, detail="Ollama service error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
def health():
    try:
        # Test if Ollama is available
        models = ollama.list()
        return {
            "status": "ok", 
            "server": "motoko-llm",
            "ollama_available": True,
            "available_models": [m["name"] for m in models.get("models", [])][:5]  # Limit response size
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "degraded",
            "server": "motoko-llm", 
            "ollama_available": False
        }

if __name__ == "__main__":
    import uvicorn
    
    # Security: Configure server properly
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"  # Listen on all interfaces for container networking
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info",
        access_log=True
    )
