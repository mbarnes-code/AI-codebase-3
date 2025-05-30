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
from services.combo_database import combo_db 

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

class ComboAnalysisRequest(BaseModel):
    commander: str
    cards: Optional[List[str]] = []

class ComboResponse(BaseModel):
    id: str
    description: str
    cards: List[str]
    power_level: int
    mana_value: int
    colors: List[str]

class ComboAnalysisResponse(BaseModel):
    commander: str
    total_combos_found: int
    commander_combos: List[ComboResponse]
    related_combos: List[ComboResponse]
    combo_pieces: List[str]
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
    """Enhanced health check endpoint"""
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
        test_commander = card_db.find_commander("Atraxa")
        health_status["services"]["django_backend"] = "connected" if test_commander else "limited"
    except Exception:
        health_status["services"]["django_backend"] = "error"
        health_status["status"] = "degraded"
    
    # Check combo database connection
    try:
        test_combos = combo_db.find_combos_for_commander(1)  # Test with ID 1
        health_status["services"]["combo_database"] = "connected"
    except Exception:
        health_status["services"]["combo_database"] = "error"
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
    """Enhanced AI Deck Builder endpoint - Phase 3 with Combo Intelligence"""
    try:
        commander_name = deck_request.commander
        format_type = deck_request.format
        strategy_focus = deck_request.strategy_focus
        budget_range = deck_request.budget_range
        
        logger.info(f"Building combo-aware deck for commander: {commander_name} with strategy: {strategy_focus}")
        
        # Step 1: Find the commander
        commander = card_db.find_commander(commander_name)
        if not commander:
            raise HTTPException(status_code=404, detail=f"Commander '{commander_name}' not found")
        
        logger.info(f"Found commander: {commander.name} - {commander.type_line}")
        
        # Step 2: Generate intelligent recommendations with combo detection
        recommendation_result = recommendation_engine.recommend_deck_with_combos(
            commander, 
            strategy_focus, 
            budget_range
        )
        
        # Step 3: Get combo analysis for this commander
        commander_combos = combo_db.find_combos_for_commander(commander.id)
        
        # Step 4: Format the enhanced response
        deck_slots_response = []
        for slot in recommendation_result.deck_slots:
            slot_response = DeckSlotResponse(
                name=slot.name,
                target_count=slot.target_count,
                cards=[_convert_card_to_response(card) for card in slot.cards[:5]],
                priority=slot.priority
            )
            deck_slots_response.append(slot_response)
        
        # Calculate advanced metrics
        all_cards = recommendation_result.recommended_cards
        mana_curve = _calculate_mana_curve(all_cards)
        color_distribution = _calculate_color_distribution(all_cards)
        
        # Create enhanced analysis with combo information
        analysis = AdvancedAnalysis(
            strategy=recommendation_result.strategy_summary,
            synergies=recommendation_result.synergy_notes,
            power_level=f"{recommendation_result.power_level}/10",
            estimated_cost=recommendation_result.estimated_cost,
            deck_slots=deck_slots_response,
            mana_curve=mana_curve,
            color_distribution=color_distribution
        )
        
        # Build final response with combo metadata
        response = DeckBuildResponse(
            commander=commander.name,
            format=format_type,
            recommended_cards=[card.name for card in all_cards[:30]],
            analysis=analysis,
            phase="3",  # Updated phase
            status="success"
        )
        
        logger.info(f"Successfully generated {len(all_cards)} combo-aware recommendations for {commander.name}")
        logger.info(f"Found {len(commander_combos)} potential combos for this commander")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building combo-aware deck: {e}")
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

@app.post("/api/ai/analyze-combos")
@limiter.limit("10/minute")
async def ai_analyze_combos(request, combo_request: ComboAnalysisRequest):
    """AI Combo Analysis endpoint - Detect combos for commanders and card pools"""
    try:
        commander_name = combo_request.commander
        additional_cards = combo_request.cards or []
        
        logger.info(f"Analyzing combos for commander: {commander_name}")
        
        # Step 1: Find the commander
        commander = card_db.find_commander(commander_name)
        if not commander:
            raise HTTPException(status_code=404, detail=f"Commander '{commander_name}' not found")
        
        # Step 2: Find combos for this commander
        commander_combos = combo_db.find_combos_for_commander(commander.id)
        
        # Step 3: Find related combos if additional cards provided
        related_combos = []
        if additional_cards:
            # Get card IDs for additional cards
            card_ids = []
            for card_name in additional_cards:
                cards = card_db.search_cards(f'name:"{card_name}"', 1)
                if cards:
                    card_ids.append(cards[0].id)
            
            if card_ids:
                related_combos = combo_db.find_combos_with_cards(card_ids)
        
        # Step 4: Get combo pieces for this color identity
        combo_pieces = combo_db.get_combo_pieces_for_colors(commander.colors)
        combo_piece_names = []
        for piece_id in combo_pieces[:10]:  # Limit to 10
            cards = card_db.search_cards(f'id:{piece_id}', 1)
            if cards:
                combo_piece_names.append(cards[0].name)
        
        # Step 5: Format response
        def format_combo(combo) -> ComboResponse:
            # Get card names for this combo
            card_names = []
            for card_id in combo.card_ids[:5]:  # Limit to 5 cards
                cards = card_db.search_cards(f'id:{card_id}', 1)
                if cards:
                    card_names.append(cards[0].name)
            
            return ComboResponse(
                id=combo.id,
                description=combo.description[:200] + "..." if len(combo.description) > 200 else combo.description,
                cards=card_names,
                power_level=combo.power_level,
                mana_value=combo.mana_value,
                colors=combo.colors
            )
        
        response = ComboAnalysisResponse(
            commander=commander.name,
            total_combos_found=len(commander_combos) + len(related_combos),
            commander_combos=[format_combo(combo) for combo in commander_combos[:10]],
            related_combos=[format_combo(combo) for combo in related_combos[:10]],
            combo_pieces=combo_piece_names,
            status="success"
        )
        
        logger.info(f"Found {len(commander_combos)} commander combos and {len(related_combos)} related combos")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing combos: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing combos")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)