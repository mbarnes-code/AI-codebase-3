# ai-workflow-fastapi/services/card_database.py

import requests
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)

@dataclass
class Card:
    """Card data structure"""
    id: int
    name: str
    oracle_text: str
    type_line: str
    mana_value: int
    identity: str
    keywords: List[str]
    price_tcgplayer: float
    legal_commander: bool
    
    @property
    def colors(self) -> List[str]:
        """Get color identity as list"""
        return [c for c in self.identity if c != 'C']
    
    @property
    def is_creature(self) -> bool:
        return "Creature" in self.type_line
    
    @property
    def is_instant_or_sorcery(self) -> bool:
        return "Instant" in self.type_line or "Sorcery" in self.type_line
    
    @property
    def is_artifact(self) -> bool:
        return "Artifact" in self.type_line
    
    @property
    def is_enchantment(self) -> bool:
        return "Enchantment" in self.type_line
    
    @property
    def is_planeswalker(self) -> bool:
        return "Planeswalker" in self.type_line
    
    @property
    def is_land(self) -> bool:
        return "Land" in self.type_line

class CardDatabaseService:
    """Service to interact with Django backend card database"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a request to the Django backend"""
        try:
            url = f"{self.backend_url}/{endpoint.lstrip('/')}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {endpoint}: {e}")
            return None
    
    def find_commander(self, name: str) -> Optional[Card]:
        """Find a commander by name"""
        try:
            # Search for the card
            params = {
                'q': f'name:"{name}" type:legendary type:creature legal:commander',
                'limit': 1
            }
            
            data = self._make_request('/cards/', params)
            if not data or not data.get('results'):
                return None
            
            card_data = data['results'][0]
            return self._parse_card(card_data)
            
        except Exception as e:
            logger.error(f"Error finding commander {name}: {e}")
            return None
    
    def get_cards_by_colors(self, colors: List[str], limit: int = 100) -> List[Card]:
        """Get cards that match the color identity"""
        try:
            # Build color identity query
            color_query = "".join(sorted(colors)) if colors else "C"
            
            params = {
                'q': f'identity:{color_query} legal:commander',
                'limit': limit,
                'ordering': '-variant_count'  # Popular cards first
            }
            
            data = self._make_request('/cards/', params)
            if not data or not data.get('results'):
                return []
            
            cards = []
            for card_data in data['results']:
                card = self._parse_card(card_data)
                if card:
                    cards.append(card)
            
            return cards
            
        except Exception as e:
            logger.error(f"Error getting cards by colors {colors}: {e}")
            return []
    
    def get_staple_cards(self, colors: List[str], card_type: str = None) -> List[Card]:
        """Get staple cards for the color identity"""
        try:
            # Build query for staples (high variant count)
            color_query = "".join(sorted(colors)) if colors else "C"
            query_parts = [f'identity:{color_query}', 'legal:commander']
            
            if card_type:
                query_parts.append(f'type:{card_type}')
            
            params = {
                'q': ' '.join(query_parts),
                'limit': 50,
                'ordering': '-variant_count'
            }
            
            data = self._make_request('/cards/', params)
            if not data or not data.get('results'):
                return []
            
            cards = []
            for card_data in data['results']:
                card = self._parse_card(card_data)
                if card and card.name not in ['Sol Ring', 'Command Tower']:  # Exclude obvious staples
                    cards.append(card)
            
            return cards[:20]  # Top 20 staples
            
        except Exception as e:
            logger.error(f"Error getting staple cards: {e}")
            return []
    
    def search_cards(self, query: str, limit: int = 20) -> List[Card]:
        """Search cards by query"""
        try:
            params = {
                'q': f'{query} legal:commander',
                'limit': limit
            }
            
            data = self._make_request('/cards/', params)
            if not data or not data.get('results'):
                return []
            
            cards = []
            for card_data in data['results']:
                card = self._parse_card(card_data)
                if card:
                    cards.append(card)
            
            return cards
            
        except Exception as e:
            logger.error(f"Error searching cards with query '{query}': {e}")
            return []
    
    def _parse_card(self, card_data: Dict) -> Optional[Card]:
        """Parse card data from Django API response"""
        try:
            return Card(
                id=card_data['id'],
                name=card_data['name'],
                oracle_text=card_data.get('oracle_text', ''),
                type_line=card_data.get('type_line', ''),
                mana_value=card_data.get('mana_value', 0),
                identity=card_data.get('identity', 'C'),
                keywords=card_data.get('keywords', []),
                price_tcgplayer=float(card_data.get('price_tcgplayer', 0)),
                legal_commander=card_data.get('legal_commander', False)
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing card data: {e}")
            return None

# Singleton instance
card_db = CardDatabaseService()