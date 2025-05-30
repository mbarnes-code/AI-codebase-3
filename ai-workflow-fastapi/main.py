from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
import os
from loguru import logger

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="AI Workflow API",
    description="FastAPI application with Ollama, Qdrant, and Redis",
    version="1.0.0"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", ""),
        decode_responses=True
    )
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    redis_client = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Workflow API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {"status": "healthy", "services": {}}
    
    # Check Redis
    try:
        if redis_client:
            redis_client.ping()
            health_status["services"]["redis"] = "connected"
        else:
            health_status["services"]["redis"] = "unavailable"
    except Exception:
        health_status["services"]["redis"] = "error"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/api/status")
@limiter.limit("10/minute")
async def api_status(request):
    """API status with rate limiting"""
    return {
        "api_version": "1.0.0",
        "status": "operational",
        "timestamp": "2025-05-29T20:52:36.856599+00:00"
    }

@app.post("/api/ai/build-deck")
@limiter.limit("5/minute")
async def ai_build_deck(request, deck_request: dict):
    """AI Deck Builder endpoint - Phase 1"""
    try:
        commander = deck_request.get("commander", "")
        format_type = deck_request.get("format", "commander")
        
        logger.info(f"Building deck for commander: {commander}")
        
        # Phase 1: Simple card recommendations
        # TODO: Replace with actual AI logic
        basic_recommendations = [
            "Sol Ring",
            "Command Tower",
            "Arcane Signet",
            "Lightning Greaves",
            "Swiftfoot Boots",
            "Kodama's Reach",
            "Cultivate",
            "Swords to Plowshares",
            "Counterspell",
            "Beast Within"
        ]
        
        response = {
            "commander": commander,
            "format": format_type,
            "recommended_cards": basic_recommendations,
            "analysis": {
                "strategy": "Basic value and utility cards",
                "synergies": [],
                "power_level": "7/10",
                "estimated_cost": "$150-250"
            },
            "phase": "1",
            "status": "success"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error building deck: {e}")
        raise HTTPException(status_code=500, detail="Error building deck")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)