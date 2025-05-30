# ai-workflow-fastapi/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
import os
from loguru import logger
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Import our new services
from services.card_database import card_db, Card
from services.recommendation_engine import recommendation_engine

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Pydantic models for API
class CardResponse(BaseModel):
    name: str
    type_line: str
    mana_value: int
    oracle_text: str
    price_tcgplayer: float

class DeckSlotResponse(BaseModel):
    name: str
    target_count: int
    cards: List[CardResponse]
    priority: int

class AdvancedAnalysis(BaseModel):
    strategy: str
    synergies: List[str]
    power_level: str
    estimated_cost: str
    deck_slots: List[DeckSlotResponse]
    mana_curve: Dict[str, int]
    color_distribution: Dict[str, int]

class DeckBuildRequest(BaseModel):
    commander: str
    format: Optional[str] = "commander"
    strategy_focus: Optional[str] = "balanced"  # balanced, aggro, control, combo
    budget_range: Optional[str] = "casual"      # budget, casual, focused, optimized

class DeckBuildResponse(BaseModel):
    commander: str
    format: str
    recommended_cards: List[str]
    analysis: AdvancedAnalysis
    phase: str
    status: str

# Create FastAPI app
app = FastAPI(
    title="AI Workflow API",
    description="FastAPI application with Ollama, Qdrant, and Redis",
    version="2.0.0"
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
    return {"message": "AI Workflow API v2.0 - Card Intelligence Ready"}

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
    
    # Check Django backend connection
    try:
        # Test commander search
        test_commander = card_db.find_commander("Atraxa")
        health_status["services"]["django_backend"] = "connected" if test_commander else "limited"
    except Exception:
        health_status["services"]["django_backend"] = "error"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/api/status")
@limiter.limit("10/minute")
async def api_status(request):
    """API status with rate limiting"""
    return {
        "api_version": "2.0.0",
        "status": "operational",
        "features": ["card_intelligence", "deck_optimization", "synergy_analysis"],
        "timestamp": "2025-05-29T20:52:36.856599+00:00"
    }

def _convert_card_to_response(card: Card) -> CardResponse:
    """Convert Card object to API response format"""
    return CardResponse(
        name=card.name,
        type_line=card.type_line,
        mana_value=card.mana_value,
        oracle_text=card.oracle_text,
        price_tcgplayer=card.price_tcgplayer
    )

def _calculate_mana_curve(cards: List[Card]) -> Dict[str, int]:
    """Calculate mana curve distribution"""
    curve = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6+": 0}
    
    for card in cards:
        if card.mana_value <= 1:
            curve["1"] += 1
        elif card.mana_value == 2:
            curve["2"] += 1
        elif card.mana_value == 3:
            curve["3"] += 1
        elif card.mana_value == 4:
            curve["4"] += 1
        elif card.mana_value == 5:
            curve["5"] += 1
        else:
            curve["6+"] += 1
    
    return curve

def _calculate_color_distribution(cards: List[Card]) -> Dict[str, int]:
    """Calculate color distribution"""
    colors = {"W": 0, "U": 0, "B": 0, "R": 0, "G": 0, "C": 0}
    
    for card in cards:
        if not card.colors:
            colors["C"] += 1
        else:
            for color in card.colors:
                if color in colors:
                    colors[color] += 1
    
    return colors

@app.post("/api/ai/build-deck")
@limiter.limit("5/minute")
async def ai_build_deck(request, deck_request: DeckBuildRequest):
    """AI Deck Builder endpoint - Phase 2 with Card Intelligence"""
    try:
        commander_name = deck_request.commander
        format_type = deck_request.format
        strategy_focus = deck_request.strategy_focus
        
        logger.info(f"Building deck for commander: {commander_name} with strategy: {strategy_focus}")
        
        # Step 1: Find the commander
        commander = card_db.find_commander(commander_name)
        if not commander:
            raise HTTPException(status_code=404, detail=f"Commander '{commander_name}' not found")
        
        logger.info(f"Found commander: {commander.name} - {commander.type_line}")
        
        # Step 2: Generate intelligent recommendations
        recommendation_result = recommendation_engine.recommend_deck(commander, strategy_focus)
        
        # Step 3: Format the response
        deck_slots_response = []
        for slot in recommendation_result.deck_slots:
            slot_response = DeckSlotResponse(
                name=slot.name,
                target_count=slot.target_count,
                cards=[_convert_card_to_response(card) for card in slot.cards[:5]],  # Limit to 5 per slot for response
                priority=slot.priority
            )
            deck_slots_response.append(slot_response)
        
        # Calculate advanced metrics
        all_cards = recommendation_result.recommended_cards
        mana_curve = _calculate_mana_curve(all_cards)
        color_distribution = _calculate_color_distribution(all_cards)
        
        # Create advanced analysis
        analysis = AdvancedAnalysis(
            strategy=recommendation_result.strategy_summary,
            synergies=recommendation_result.synergy_notes,
            power_level=f"{recommendation_result.power_level}/10",
            estimated_cost=recommendation_result.estimated_cost,
            deck_slots=deck_slots_response,
            mana_curve=mana_curve,
            color_distribution=color_distribution
        )
        
        # Build final response
        response = DeckBuildResponse(
            commander=commander.name,
            format=format_type,
            recommended_cards=[card.name for card in all_cards[:30]],  # Top 30 recommendations
            analysis=analysis,
            phase="2",
            status="success"
        )
        
        logger.info(f"Successfully generated {len(all_cards)} recommendations for {commander.name}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building deck: {e}")
        raise HTTPException(status_code=500, detail="Error building deck")

@app.get("/api/cards/search")
@limiter.limit("20/minute")
async def search_cards(request, q: str, limit: int = 20):
    """Search cards endpoint"""
    try:
        cards = card_db.search_cards(q, limit)
        return {
            "query": q,
            "count": len(cards),
            "cards": [_convert_card_to_response(card) for card in cards]
        }
    except Exception as e:
        logger.error(f"Error searching cards: {e}")
        raise HTTPException(status_code=500, detail="Error searching cards")

@app.get("/api/cards/commander/{name}")
@limiter.limit("10/minute") 
async def get_commander(request, name: str):
    """Get commander details"""
    try:
        commander = card_db.find_commander(name)
        if not commander:
            raise HTTPException(status_code=404, detail=f"Commander '{name}' not found")
        
        return {
            "commander": _convert_card_to_response(commander),
            "colors": commander.colors,
            "identity": commander.identity
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commander: {e}")
        raise HTTPException(status_code=500, detail="Error getting commander")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)