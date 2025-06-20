# commander-spellbook-backend-master/backend/spellbook/services/ai_service.py

import requests
import logging
from typing import Dict, Optional, Any
from django.conf import settings

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass

class AIService:
    """Service to interact with the FastAPI AI service"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'AI_SERVICE_URL', 'http://localhost:8001')
        self.timeout = 30
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def health_check(self) -> bool:
        """Check if AI service is healthy"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.warning(f"AI service health check failed: {e}")
            return False
    
    def build_deck(self, commander: str, format_type: str = "commander", 
                   strategy_focus: str = "balanced", budget_range: str = "casual") -> Optional[Dict[str, Any]]:
        """Build a deck using the AI service"""
        try:
            payload = {
                "commander": commander,
                "format": format_type,
                "strategy_focus": strategy_focus,
                "budget_range": budget_range
            }
            
            logger.info(f"Calling AI service to build deck for {commander}")
            
            response = self.session.post(
                f"{self.base_url}/api/ai/build-deck",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                logger.warning(f"Commander '{commander}' not found in AI service")
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"AI service timeout when building deck for {commander}")
            raise AIServiceError("AI service request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"AI service request failed: {e}")
            raise AIServiceError(f"AI service unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling AI service: {e}")
            raise AIServiceError(f"Unexpected error: {str(e)}")
    
    def search_cards(self, query: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """Search cards using the AI service"""
        try:
            params = {
                'q': query,
                'limit': limit
            }
            
            response = self.session.get(
                f"{self.base_url}/api/cards/search",
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching cards: {e}")
            return None
    
    def get_commander_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get commander information from AI service"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/cards/commander/{name}",
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting commander info: {e}")
            return None

# Singleton instance
ai_service = AIService()