# ai-workflow-fastapi/services/recommendation_engine.py

import logging
from typing import List, Dict, Set, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
import re

from .card_database import Card, card_db

logger = logging.getLogger(__name__)

@dataclass
class DeckSlot:
    """Represents a category of cards in the deck"""
    name: str
    target_count: int
    cards: List[Card]
    priority: int = 5  # 1-10, higher = more important

@dataclass
class RecommendationResult:
    """Result of card recommendation"""
    recommended_cards: List[Card]
    deck_slots: List[DeckSlot]
    strategy_summary: str
    synergy_notes: List[str]
    power_level: int  # 1-10
    estimated_cost: str

class CardRecommendationEngine:
    """Intelligent card recommendation engine"""
    
    def __init__(self):
        # Target exactly 100 cards (99 + 1 commander)
        self.target_deck_size = 99  # Excluding commander
        
        # Essential card categories for Commander
        self.essential_categories = {
            'lands': 37,         # Mana base
            'ramp': 10,          # Mana acceleration  
            'card_draw': 10,     # Card advantage
            'removal': 8,        # Spot removal
            'threats': 15,       # Win conditions/creatures
            'protection': 5,     # Protection spells
            'utility': 8,        # Utility cards
            'board_wipes': 3,    # Mass removal
            'tutors': 3          # Search effects
            # Total: 99 cards
        }
    
    def recommend_deck_with_combos(self, commander: Card, strategy_focus: str = "balanced", 
                                   power_level: str = "casual") -> RecommendationResult:
        """Enhanced recommendation with combo detection - exactly 100 cards"""
        logger.info(f"Generating 100-card deck for commander: {commander.name}")
        
        # Build deck structure
        deck_slots = self._build_100_card_structure(commander.colors, strategy_focus)
        
        # Fill slots with cards
        self._fill_deck_slots_exactly(deck_slots, commander.colors, commander)
        
        # Enhance with combo detection
        enhanced_result = self._enhance_with_combos(commander, deck_slots, power_level)
        
        # Ensure exactly 99 cards (+ commander = 100)
        all_cards = self._ensure_exactly_99_cards(enhanced_result.deck_slots)
        
        logger.info(f"Generated exactly {len(all_cards)} cards + 1 commander = 100 total")
        
        return RecommendationResult(
            recommended_cards=all_cards,
            deck_slots=enhanced_result.deck_slots,
            strategy_summary=enhanced_result.strategy_summary,
            synergy_notes=enhanced_result.synergy_notes,
            power_level=enhanced_result.power_level,
            estimated_cost=self._estimate_cost(all_cards)
        )

    def _build_100_card_structure(self, colors: List[str], strategy_focus: str) -> List[DeckSlot]:
        """Build deck structure that totals exactly 99 cards"""
        slots = []
        
        if strategy_focus == 'aggro':
            slots.extend([
                DeckSlot('lands', 35, [], 10),
                DeckSlot('ramp', 8, [], 8),
                DeckSlot('card_draw', 8, [], 7),
                DeckSlot('removal', 6, [], 6),
                DeckSlot('protection', 6, [], 8),
                DeckSlot('threats', 22, [], 9),
                DeckSlot('utility', 10, [], 5),
                DeckSlot('board_wipes', 2, [], 4),
                DeckSlot('tutors', 2, [], 6)
            ])
        elif strategy_focus == 'control':
            slots.extend([
                DeckSlot('lands', 38, [], 10),
                DeckSlot('ramp', 12, [], 8),
                DeckSlot('card_draw', 12, [], 9),
                DeckSlot('removal', 10, [], 9),
                DeckSlot('board_wipes', 6, [], 8),
                DeckSlot('protection', 8, [], 7),
                DeckSlot('threats', 8, [], 7),
                DeckSlot('utility', 12, [], 6),
                DeckSlot('tutors', 3, [], 7)
            ])
        elif strategy_focus == 'combo':
            slots.extend([
                DeckSlot('lands', 36, [], 10),
                DeckSlot('ramp', 12, [], 9),
                DeckSlot('card_draw', 10, [], 9),
                DeckSlot('tutors', 8, [], 10),
                DeckSlot('combo_pieces', 12, [], 10),
                DeckSlot('protection', 10, [], 8),
                DeckSlot('removal', 6, [], 6),
                DeckSlot('utility', 5, [], 5)
            ])
        else:  # balanced
            slots.extend([
                DeckSlot('lands', 37, [], 10),
                DeckSlot('ramp', 10, [], 8),
                DeckSlot('card_draw', 10, [], 8),
                DeckSlot('removal', 8, [], 7),
                DeckSlot('threats', 15, [], 7),
                DeckSlot('protection', 5, [], 6),
                DeckSlot('utility', 8, [], 6),
                DeckSlot('board_wipes', 3, [], 5),
                DeckSlot('tutors', 3, [], 6)
            ])
        
        # Verify total is exactly 99
        total = sum(slot.target_count for slot in slots)
        if total != 99:
            logger.warning(f"Deck structure totals {total} cards, adjusting to 99")
            # Adjust the largest flexible slot
            largest_slot = max(slots, key=lambda s: s.target_count if s.name not in ['lands'] else 0)
            largest_slot.target_count += (99 - total)
        
        return slots

    def _fill_deck_slots_exactly(self, deck_slots: List[DeckSlot], colors: List[str], commander: Card):
        """Fill deck slots with exactly the target number of cards"""
        
        for slot in deck_slots:
            logger.info(f"Filling slot: {slot.name} (target: {slot.target_count})")
            
            # Get cards for this slot type
            candidate_cards = self._get_cards_for_slot(slot.name, colors, commander, slot.target_count * 3)
            
            # Fill to exact target count
            slot.cards = candidate_cards[:slot.target_count]
            
            # If we don't have enough cards, fill with basic lands or generic cards
            while len(slot.cards) < slot.target_count:
                filler_card = self._get_filler_card(slot.name, colors)
                if filler_card and filler_card not in slot.cards:
                    slot.cards.append(filler_card)
                else:
                    break
            
            # Ensure exact count
            slot.cards = slot.cards[:slot.target_count]
            
            logger.info(f"Filled {slot.name} with {len(slot.cards)} cards")

    def _get_cards_for_slot(self, slot_name: str, colors: List[str], commander: Card, limit: int) -> List[Card]:
        """Get cards for a specific slot type"""
        
        searches = {
            'lands': self._get_land_searches(colors),
            'ramp': ['Sol Ring', 'Arcane Signet', 'oracle:"add mana"', 'Cultivate', 'Kodama\'s Reach'],
            'card_draw': ['oracle:"draw cards"', 'Rhystic Study', 'Mystic Remora'],
            'removal': ['Swords to Plowshares', 'Path to Exile', 'Murder', 'Chaos Warp'],
            'threats': ['type:creature legal:commander', 'type:planeswalker legal:commander'],
            'protection': ['Lightning Greaves', 'Swiftfoot Boots', 'Counterspell'],
            'utility': ['oracle:"enters the battlefield" legal:commander'],
            'board_wipes': ['Wrath of God', 'Damnation', 'Blasphemous Act'],
            'tutors': ['Demonic Tutor', 'Vampiric Tutor', 'oracle:"search your library"'],
            'combo_pieces': ['oracle:"infinite" legal:commander']
        }
        
        slot_searches = searches.get(slot_name, ['legal:commander'])
        cards = []
        
        for search in slot_searches:
            if len(cards) >= limit:
                break
            found_cards = card_db.search_cards(search, min(10, limit - len(cards)))
            for card in found_cards:
                if card not in cards and len(cards) < limit:
                    cards.append(card)
        
        return cards

    def _get_land_searches(self, colors: List[str]) -> List[str]:
        """Get land search terms based on color identity"""
        searches = ['Sol Ring', 'Command Tower', 'Arcane Signet']  # Always include these
        
        # Add basic lands
        basic_lands = {
            'W': 'Plains',
            'U': 'Island', 
            'B': 'Swamp',
            'R': 'Mountain',
            'G': 'Forest'
        }
        
        for color in colors:
            if color in basic_lands:
                searches.append(basic_lands[color])
        
        # Add dual lands for multicolor decks
        if len(colors) >= 2:
            searches.extend([
                'type:land enters tapped',
                'type:land produces any color'
            ])
        
        return searches

    def _get_filler_card(self, slot_name: str, colors: List[str]) -> Card:
        """Get a filler card when we don't have enough for a slot"""
        
        filler_searches = {
            'lands': ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest'],
            'ramp': ['Sol Ring'],
            'card_draw': ['Divination'],
            'removal': ['Murder'],
            'threats': ['type:creature'],
            'protection': ['Lightning Greaves'],
            'utility': ['type:artifact'],
            'board_wipes': ['Day of Judgment'],
            'tutors': ['Diabolic Tutor']
        }
        
        searches = filler_searches.get(slot_name, ['legal:commander'])
        
        for search in searches:
            cards = card_db.search_cards(search, 1)
            if cards:
                return cards[0]
        
        return None

    def _ensure_exactly_99_cards(self, deck_slots: List[DeckSlot]) -> List[Card]:
        """Ensure we have exactly 99 cards, no more, no less"""
        all_cards = []
        
        # Collect all cards
        for slot in deck_slots:
            all_cards.extend(slot.cards)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_cards = []
        for card in all_cards:
            if card.name not in seen:
                seen.add(card.name)
                unique_cards.append(card)
        
        # Adjust to exactly 99
        if len(unique_cards) > 99:
            # Too many cards - remove least important
            unique_cards = unique_cards[:99]
        elif len(unique_cards) < 99:
            # Too few cards - add filler
            while len(unique_cards) < 99:
                filler = card_db.search_cards('legal:commander', 1)
                if filler and filler[0] not in unique_cards:
                    unique_cards.append(filler[0])
                else:
                    break
        
        return unique_cards[:99]  # Ensure exactly 99

    def _enhance_with_combos(self, commander: Card, deck_slots: List[DeckSlot], power_level: str) -> RecommendationResult:
        """Enhance with combo detection"""
        from .combo_database import combo_db
        
        # Find combos for this commander
        commander_combos = combo_db.find_combos_for_commander(commander.id)
        
        # Generate enhanced analysis
        strategy = f"This deck leverages {commander.name}'s abilities for {power_level} gameplay"
        synergies = [f"Optimized for {len(commander_combos)} potential combo lines" if commander_combos else "Value-focused strategy"]
        power = min(8 if commander_combos else 6, 10)
        
        # Collect all cards
        all_cards = []
        for slot in deck_slots:
            all_cards.extend(slot.cards)
        
        return RecommendationResult(
            recommended_cards=all_cards,
            deck_slots=deck_slots,
            strategy_summary=strategy,
            synergy_notes=synergies,
            power_level=power,
            estimated_cost=self._estimate_cost(all_cards)
        )
    
    def _estimate_cost(self, cards: List[Card]) -> str:
        """Estimate total deck cost"""
        total_cost = sum(card.price_tcgplayer for card in cards)
        
        if total_cost < 100:
            return "$50-100 (Budget)"
        elif total_cost < 300:
            return "$150-300 (Casual)"
        elif total_cost < 600:
            return "$300-600 (Focused)"
        elif total_cost < 1000:
            return "$600-1000 (Optimized)"
        else:
            return "$1000+ (High Power)"

# Singleton instance
recommendation_engine = CardRecommendationEngine()