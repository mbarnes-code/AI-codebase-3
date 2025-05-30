# ai-workflow-fastapi/services/combo_database.py

import requests
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)

@dataclass
class Combo:
    """Combo data structure"""
    id: str
    description: str
    commander_ids: List[int]
    card_ids: List[int]
    feature_ids: List[int]
    mana_value: int
    power_level: int
    identity: str
    popularity: Optional[int] = None
    
    @property
    def colors(self) -> List[str]:
        """Get color identity as list"""
        return [c for c in self.identity if c != 'C']

@dataclass
class Variant:
    """Variant data structure"""
    id: str
    combo_id: str
    cards: List[int]
    description: str
    mana_needed: str
    status: str
    popularity: Optional[int] = None

class ComboDatabaseService:
    """Service to interact with Django backend combo database"""
    
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
    
    def find_combos_for_commander(self, commander_id: int) -> List[Combo]:
        """Find combos that include this commander"""
        try:
            params = {
                'q': f'card:{commander_id}',
                'limit': 50
            }
            
            data = self._make_request('/variants/', params)
            if not data or not data.get('results'):
                return []
            
            combos = []
            for variant_data in data['results']:
                combo = self._parse_combo_from_variant(variant_data)
                if combo:
                    combos.append(combo)
            
            return combos
            
        except Exception as e:
            logger.error(f"Error finding combos for commander {commander_id}: {e}")
            return []
    
    def find_combos_with_cards(self, card_ids: List[int]) -> List[Combo]:
        """Find combos that use these cards"""
        try:
            # Build query to find variants with these cards
            card_queries = [f'card:{card_id}' for card_id in card_ids]
            query = ' OR '.join(card_queries)
            
            params = {
                'q': query,
                'limit': 100
            }
            
            data = self._make_request('/variants/', params)
            if not data or not data.get('results'):
                return []
            
            combos = []
            for variant_data in data['results']:
                combo = self._parse_combo_from_variant(variant_data)
                if combo:
                    combos.append(combo)
            
            return combos
            
        except Exception as e:
            logger.error(f"Error finding combos with cards {card_ids}: {e}")
            return []
    
    def get_combo_pieces_for_colors(self, colors: List[str]) -> List[int]:
        """Get popular combo pieces for these colors"""
        try:
            color_query = "".join(sorted(colors)) if colors else "C"
            
            params = {
                'q': f'identity:{color_query}',
                'limit': 50,
                'ordering': '-popularity'
            }
            
            data = self._make_request('/variants/', params)
            if not data or not data.get('results'):
                return []
            
            # Extract unique card IDs from popular combos
            combo_pieces = set()
            for variant in data['results']:
                for card_usage in variant.get('uses', []):
                    combo_pieces.add(card_usage['card']['id'])
            
            return list(combo_pieces)
            
        except Exception as e:
            logger.error(f"Error getting combo pieces for colors {colors}: {e}")
            return []
    
    def get_meta_staples(self, colors: List[str], power_level: str = "casual") -> List[int]:
        """Get meta staple cards for color identity and power level"""
        try:
            color_query = "".join(sorted(colors)) if colors else "C"
            
            # Adjust query based on power level
            if power_level == "competitive":
                params = {
                    'q': f'identity:{color_query} legal:commander',
                    'limit': 30,
                    'ordering': '-popularity'
                }
            else:
                params = {
                    'q': f'identity:{color_query} legal:commander',
                    'limit': 20,
                    'ordering': '-variant_count'
                }
            
            data = self._make_request('/cards/', params)
            if not data or not data.get('results'):
                return []
            
            return [card['id'] for card in data['results']]
            
        except Exception as e:
            logger.error(f"Error getting meta staples: {e}")
            return []
    
    def _parse_combo_from_variant(self, variant_data: Dict) -> Optional[Combo]:
        """Parse combo data from variant response"""
        try:
            return Combo(
                id=variant_data['id'],
                description=variant_data.get('description', ''),
                commander_ids=[
                    card['card']['id'] for card in variant_data.get('uses', [])
                    if card.get('must_be_commander', False)
                ],
                card_ids=[
                    card['card']['id'] for card in variant_data.get('uses', [])
                ],
                feature_ids=[
                    feature['feature']['id'] for feature in variant_data.get('produces', [])
                ],
                mana_value=variant_data.get('mana_value_needed', 0),
                power_level=self._estimate_power_from_variant(variant_data),
                identity=variant_data.get('identity', 'C'),
                popularity=variant_data.get('popularity')
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing combo data: {e}")
            return None
    
    def _estimate_power_from_variant(self, variant_data: Dict) -> int:
        """Estimate power level from variant data"""
        # Simple heuristic based on mana value and card count
        mana_value = variant_data.get('mana_value_needed', 0)
        card_count = len(variant_data.get('uses', []))
        
        if mana_value <= 3 and card_count <= 2:
            return 8  # High power
        elif mana_value <= 5 and card_count <= 3:
            return 6  # Medium-high power
        elif mana_value <= 7:
            return 4  # Medium power
        else:
            return 2  # Lower power

# Singleton instance
combo_db = ComboDatabaseService()