import requests
import logging
from django.conf import settings
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AIServiceClient:
    """Client for FastAPI AI service"""
    
    def __init__(self):
        # You'll need to add this to your Django settings
        self.ai_service_url = getattr(settings, 'AI_SERVICE_URL', 'http://localhost:8001')
        self.timeout = 30
    
    def build_deck(self, commander: str, format_type: str = "commander") -> Optional[Dict]:
        """Request AI deck building from FastAPI service"""
        try:
            url = f"{self.ai_service_url}/api/ai/build-deck"
            
            payload = {
                "commander": commander,
                "format": format_type
            }
            
            logger.info(f"Calling AI service: {url}")
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"AI service error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to AI service: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling AI service: {e}")
            return None
    
    def health_check(self) -> bool:
        """Check if AI service is available"""
        try:
            url = f"{self.ai_service_url}/health"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False


# Singleton instance
ai_service = AIServiceClient()