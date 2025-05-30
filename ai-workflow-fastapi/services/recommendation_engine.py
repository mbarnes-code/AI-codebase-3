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
        self.mana_curve_targets = {
            1: 8,   # 1 CMC
            2: 12,  # 2 CMC  
            3: 15,  # 3 CMC
            4: 10,  # 4 CMC
            5: 6,   # 5 CMC
            6: 4,   # 6+ CMC
        }
        
        # Essential card categories
        self.essential_categories = {
            'ramp': 12,          # Mana acceleration
            'card_draw': 10,     # Card advantage
            'removal': 8,        # Spot removal
            'board_wipes': 3,    # Mass removal
            'protection': 5,     # Protection spells
            'lands': 37,         # Mana base
            'win_cons': 8,       # Win conditions
            'utility': 7         # Utility cards
        }
    
    def recommend_deck(self, commander: Card, strategy_focus: str = "balanced") -> RecommendationResult:
        """Main recommendation function"""
        logger.info(f"Generating recommendations for commander: {commander.name}")
        
        # Analyze commander
        commander_analysis = self._analyze_commander(commander)
        
        # Get color identity
        colors = commander.colors
        
        # Build deck slots
        deck_slots = self._build_deck_structure(colors, commander_analysis, strategy_focus)
        
        # Fill slots with cards
        self._fill_deck_slots(deck_slots, colors, commander_analysis)
        
        # Generate all recommendations
        all_cards = []
        for slot in deck_slots:
            all_cards.extend(slot.cards)
        
        # Create summary
        strategy_summary = self._generate_strategy_summary(commander, commander_analysis, strategy_focus)
        synergy_notes = self._generate_synergy_notes(commander, all_cards)
        power_level = self._estimate_power_level(all_cards)
        estimated_cost = self._estimate_cost(all_cards)
        
        return RecommendationResult(
            recommended_cards=all_cards,
            deck_slots=deck_slots,
            strategy_summary=strategy_summary,
            synergy_notes=synergy_notes,
            power_level=power_level,
            estimated_cost=estimated_cost
        )
    
    def recommend_deck_with_combos(self, commander: Card, strategy_focus: str = "balanced", 
                                   power_level: str = "casual") -> RecommendationResult:
        """Enhanced recommendation with combo detection"""
        logger.info(f"Generating combo-aware recommendations for commander: {commander.name}")
        
        # Get basic recommendations
        basic_result = self.recommend_deck(commander, strategy_focus)
        
        # Enhance with combo detection
        enhanced_result = self._enhance_with_combos(commander, basic_result, power_level)
        
        return enhanced_result

    def _enhance_with_combos(self, commander: Card, basic_result: RecommendationResult, 
                            power_level: str) -> RecommendationResult:
        """Enhance recommendations with combo detection"""
        
        # Import here to avoid circular imports
        from .combo_database import combo_db
        
        # Find combos for this commander
        commander_combos = combo_db.find_combos_for_commander(commander.id)
        
        # Get meta staples for the color identity
        meta_staples = combo_db.get_meta_staples(commander.colors, power_level)
        
        # Enhance deck slots with combo-aware cards
        enhanced_slots = self._enhance_deck_slots_with_combos(
            basic_result.deck_slots, 
            commander_combos, 
            meta_staples, 
            commander.colors,
            power_level
        )
        
        # Generate enhanced analysis
        enhanced_strategy = self._generate_combo_aware_strategy(commander, commander_combos)
        enhanced_synergies = self._generate_combo_synergies(commander_combos, basic_result.synergy_notes)
        enhanced_power_level = self._calculate_combo_power_level(commander_combos, basic_result.power_level)
        
        # Collect all cards
        all_cards = []
        for slot in enhanced_slots:
            all_cards.extend(slot.cards)
        
        return RecommendationResult(
            recommended_cards=all_cards,
            deck_slots=enhanced_slots,
            strategy_summary=enhanced_strategy,
            synergy_notes=enhanced_synergies,
            power_level=enhanced_power_level,
            estimated_cost=self._estimate_cost(all_cards)
        )

    def _enhance_deck_slots_with_combos(self, basic_slots: List[DeckSlot], combos: List, 
                                       meta_staples: List[int], colors: List[str], 
                                       power_level: str) -> List[DeckSlot]:
        """Enhance deck slots with combo pieces and meta staples"""
        
        enhanced_slots = []
        
        for slot in basic_slots:
            enhanced_slot = DeckSlot(
                name=slot.name,
                target_count=slot.target_count,
                cards=slot.cards.copy(),
                priority=slot.priority
            )
            
            # Add combo pieces to relevant slots
            if slot.name in ['threats', 'win_cons', 'combo_pieces']:
                combo_cards = self._get_combo_cards_for_slot(combos, slot.name, colors)
                enhanced_slot.cards.extend(combo_cards)
            
            # Add meta staples to appropriate slots
            if slot.name in ['ramp', 'card_draw', 'removal']:
                staple_cards = self._get_meta_staples_for_slot(meta_staples, slot.name)
                enhanced_slot.cards.extend(staple_cards)
            
            # Remove duplicates and limit to target count
            seen_names = set()
            unique_cards = []
            for card in enhanced_slot.cards:
                if card.name not in seen_names:
                    unique_cards.append(card)
                    seen_names.add(card.name)
            
            enhanced_slot.cards = unique_cards[:slot.target_count]
            enhanced_slots.append(enhanced_slot)
        
        # Add new combo-specific slot if we found good combos
        if combos and power_level in ['focused', 'optimized']:
            combo_slot = self._create_combo_slot(combos, colors)
            if combo_slot.cards:
                enhanced_slots.append(combo_slot)
        
        return enhanced_slots

    def _get_combo_cards_for_slot(self, combos: List, slot_name: str, colors: List[str]) -> List[Card]:
        """Get combo cards appropriate for this slot"""
        combo_cards = []
        
        # Get unique card IDs from combos
        combo_card_ids = set()
        for combo in combos[:5]:  # Limit to top 5 combos
            combo_card_ids.update(combo.card_ids)
        
        # Search for these cards in our database
        for card_id in list(combo_card_ids)[:10]:  # Limit search
            cards = card_db.search_cards(f'id:{card_id}', 1)
            if cards:
                combo_cards.extend(cards)
        
        return combo_cards[:5]  # Limit results

    def _get_meta_staples_for_slot(self, meta_staples: List[int], slot_name: str) -> List[Card]:
        """Get meta staple cards for this slot"""
        staple_cards = []
        
        # Map slot types to card type searches
        slot_searches = {
            'ramp': ['Sol Ring', 'Arcane Signet', 'oracle:"add mana"'],
            'card_draw': ['oracle:"draw cards"', 'Rhystic Study'],
            'removal': ['Swords to Plowshares', 'oracle:"destroy target"']
        }
        
        if slot_name in slot_searches:
            for search in slot_searches[slot_name][:2]:  # Limit searches
                cards = card_db.search_cards(search, 2)
                staple_cards.extend(cards)
        
        return staple_cards[:3]  # Limit results

    def _create_combo_slot(self, combos: List, colors: List[str]) -> DeckSlot:
        """Create a dedicated combo slot"""
        combo_cards = []
        
        # Get the best combo pieces
        for combo in combos[:3]:  # Top 3 combos
            for card_id in combo.card_ids[:2]:  # 2 cards per combo
                cards = card_db.search_cards(f'id:{card_id}', 1)
                if cards:
                    combo_cards.extend(cards)
        
        return DeckSlot(
            name='combo_enablers',
            target_count=6,
            cards=combo_cards[:6],
            priority=9
        )

    def _generate_combo_aware_strategy(self, commander: Card, combos: List) -> str:
        """Generate strategy summary including combo information"""
        base_strategy = f"This deck leverages {commander.name}'s abilities"
        
        if combos:
            combo_count = len(combos)
            if combo_count >= 3:
                base_strategy += f" alongside {combo_count} potential combo lines"
            else:
                base_strategy += f" with {combo_count} combo synergies"
            
            # Mention top combo
            if combos[0].description:
                base_strategy += f". Primary combo: {combos[0].description[:100]}..."
        
        base_strategy += ". The deck balances value generation with combo potential for versatile gameplay."
        
        return base_strategy

    def _generate_combo_synergies(self, combos: List, base_synergies: List[str]) -> List[str]:
        """Generate synergy notes including combo analysis"""
        enhanced_synergies = base_synergies.copy()
        
        if combos:
            combo_power_levels = [combo.power_level for combo in combos]
            avg_power = sum(combo_power_levels) / len(combo_power_levels)
            
            if avg_power >= 7:
                enhanced_synergies.append("Contains high-power combo lines for competitive play")
            elif avg_power >= 5:
                enhanced_synergies.append("Features medium-power combos for focused gameplay")
            else:
                enhanced_synergies.append("Includes casual combo synergies for fun interactions")
            
            # Add specific combo type notes
            mana_values = [combo.mana_value for combo in combos if combo.mana_value > 0]
            if mana_values:
                avg_mana = sum(mana_values) / len(mana_values)
                if avg_mana <= 4:
                    enhanced_synergies.append("Low mana value combos enable early game wins")
                elif avg_mana <= 6:
                    enhanced_synergies.append("Mid-range combo costs fit well in the mana curve")
        
        return enhanced_synergies[:6]  # Limit to 6 synergies

    def _calculate_combo_power_level(self, combos: List, base_power: int) -> int:
        """Calculate power level including combo presence"""
        if not combos:
            return base_power
        
        combo_power_levels = [combo.power_level for combo in combos]
        max_combo_power = max(combo_power_levels)
        
        # Boost power level based on combo strength
        if max_combo_power >= 8:
            return min(base_power + 2, 10)
        elif max_combo_power >= 6:
            return min(base_power + 1, 10)
        else:
            return base_power
    
    def _analyze_commander(self, commander: Card) -> Dict[str, Any]:
        """Analyze commander to understand deck strategy"""
        analysis = {
            'themes': [],
            'keywords': commander.keywords,
            'power_level': 'mid',
            'strategy_type': 'value',
            'mana_value': commander.mana_value,
            'colors': commander.colors
        }
        
        oracle_text = commander.oracle_text.lower()
        
        # Detect themes from oracle text
        theme_patterns = {
            'artifacts': ['artifact', 'equipment', 'vehicles'],
            'graveyard': ['graveyard', 'dies', 'death', 'sacrifice'],
            'tokens': ['token', 'create', 'populate'],
            'counters': ['counter', '+1/+1', 'proliferate'],
            'spells': ['instant', 'sorcery', 'spell'],
            'tribal': ['tribal', 'creature type'],
            'voltron': ['equipment', 'aura', 'attach'],
            'control': ['counter', 'draw', 'return'],
            'aggro': ['attack', 'combat', 'damage'],
            'combo': ['infinite', 'win the game', 'exile'],
            'ramp': ['land', 'mana', 'search your library']
        }
        
        for theme, patterns in theme_patterns.items():
            if any(pattern in oracle_text for pattern in patterns):
                analysis['themes'].append(theme)
        
        # Determine strategy type
        if 'combo' in analysis['themes']:
            analysis['strategy_type'] = 'combo'
        elif 'aggro' in analysis['themes'] or 'voltron' in analysis['themes']:
            analysis['strategy_type'] = 'aggro'
        elif 'control' in analysis['themes']:
            analysis['strategy_type'] = 'control'
        else:
            analysis['strategy_type'] = 'value'
        
        return analysis
    
    def _build_deck_structure(self, colors: List[str], commander_analysis: Dict, strategy_focus: str) -> List[DeckSlot]:
        """Build the deck structure with target slot counts"""
        slots = []
        
        # Adjust counts based on strategy
        if commander_analysis['strategy_type'] == 'aggro':
            slots.extend([
                DeckSlot('lands', 35, [], 10),
                DeckSlot('ramp', 8, [], 8),
                DeckSlot('card_draw', 8, [], 7),
                DeckSlot('removal', 6, [], 6),
                DeckSlot('protection', 8, [], 8),
                DeckSlot('threats', 20, [], 9),
                DeckSlot('support', 14, [], 5)
            ])
        elif commander_analysis['strategy_type'] == 'control':
            slots.extend([
                DeckSlot('lands', 38, [], 10),
                DeckSlot('ramp', 10, [], 8),
                DeckSlot('card_draw', 12, [], 9),
                DeckSlot('removal', 12, [], 9),
                DeckSlot('board_wipes', 5, [], 8),
                DeckSlot('win_cons', 6, [], 7),
                DeckSlot('utility', 16, [], 6)
            ])
        elif commander_analysis['strategy_type'] == 'combo':
            slots.extend([
                DeckSlot('lands', 36, [], 10),
                DeckSlot('ramp', 12, [], 9),
                DeckSlot('card_draw', 12, [], 9),
                DeckSlot('tutors', 8, [], 9),
                DeckSlot('combo_pieces', 15, [], 10),
                DeckSlot('protection', 8, [], 8),
                DeckSlot('removal', 8, [], 6)
            ])
        else:  # value/balanced
            slots.extend([
                DeckSlot('lands', 37, [], 10),
                DeckSlot('ramp', 12, [], 8),
                DeckSlot('card_draw', 10, [], 8),
                DeckSlot('removal', 8, [], 7),
                DeckSlot('threats', 18, [], 7),
                DeckSlot('utility', 14, [], 6)
            ])
        
        return slots
    
    def _fill_deck_slots(self, deck_slots: List[DeckSlot], colors: List[str], commander_analysis: Dict):
        """Fill deck slots with appropriate cards"""
        
        for slot in deck_slots:
            logger.info(f"Filling slot: {slot.name} (target: {slot.target_count})")
            
            if slot.name == 'lands':
                slot.cards = self._get_mana_base(colors, slot.target_count)
            elif slot.name == 'ramp':
                slot.cards = self._get_ramp_cards(colors, slot.target_count)
            elif slot.name == 'card_draw':
                slot.cards = self._get_card_draw(colors, slot.target_count)
            elif slot.name == 'removal':
                slot.cards = self._get_removal(colors, slot.target_count)
            elif slot.name == 'board_wipes':
                slot.cards = self._get_board_wipes(colors, slot.target_count)
            elif slot.name == 'protection':
                slot.cards = self._get_protection(colors, slot.target_count)
            elif slot.name == 'threats':
                slot.cards = self._get_threats(colors, commander_analysis, slot.target_count)
            elif slot.name == 'win_cons':
                slot.cards = self._get_win_conditions(colors, slot.target_count)
            elif slot.name == 'tutors':
                slot.cards = self._get_tutors(colors, slot.target_count)
            elif slot.name == 'combo_pieces':
                slot.cards = self._get_combo_pieces(colors, commander_analysis, slot.target_count)
            else:  # utility, support, etc.
                slot.cards = self._get_utility_cards(colors, slot.target_count)
    
    def _get_mana_base(self, colors: List[str], count: int) -> List[Card]:
        """Get mana base recommendations"""
        lands = []
        
        # Essential lands
        essential_searches = [
            'Command Tower',
            'Sol Ring',  # Not a land but essential
            'Arcane Signet'
        ]
        
        # Color-specific lands
        if len(colors) >= 2:
            essential_searches.extend([
                f'type:land enters tapped identity:{"".join(colors)}',
                f'type:land identity:{"".join(colors)} -type:basic'
            ])
        
        # Add basics
        if colors:
            for color in colors:
                if color == 'W':
                    essential_searches.append('Plains')
                elif color == 'U':
                    essential_searches.append('Island')
                elif color == 'B':
                    essential_searches.append('Swamp')
                elif color == 'R':
                    essential_searches.append('Mountain')
                elif color == 'G':
                    essential_searches.append('Forest')
        
        # Search for lands
        for search in essential_searches[:count]:
            cards = card_db.search_cards(search, 5)
            if cards:
                lands.extend(cards[:2])
        
        return lands[:count]
    
    def _get_ramp_cards(self, colors: List[str], count: int) -> List[Card]:
        """Get ramp/acceleration cards"""
        ramp_searches = [
            'Sol Ring',
            'Arcane Signet',
            'type:artifact cmc:2 oracle:"add mana"',
            'oracle:"search your library for a land"',
            'oracle:"ramp" legal:commander'
        ]
        
        if 'G' in colors:
            ramp_searches.extend([
                'Cultivate',
                'Kodama\'s Reach',
                'Rampant Growth',
                'Three Visits'
            ])
        
        ramp_cards = []
        for search in ramp_searches:
            cards = card_db.search_cards(search, 3)
            ramp_cards.extend(cards)
        
        return ramp_cards[:count]
    
    def _get_card_draw(self, colors: List[str], count: int) -> List[Card]:
        """Get card draw recommendations"""
        draw_searches = [
            'oracle:"draw cards" legal:commander',
            'oracle:"draw a card" legal:commander'
        ]
        
        if 'U' in colors:
            draw_searches.extend([
                'Rhystic Study',
                'Mystic Remora',
                'Divination'
            ])
        
        if 'G' in colors:
            draw_searches.extend([
                'Beast Whisperer',
                'Guardian Project'
            ])
        
        draw_cards = []
        for search in draw_searches:
            cards = card_db.search_cards(search, 3)
            draw_cards.extend(cards)
        
        return draw_cards[:count]
    
    def _get_removal(self, colors: List[str], count: int) -> List[Card]:
        """Get removal cards"""
        removal_searches = [
            'oracle:"destroy target" legal:commander',
            'oracle:"exile target" legal:commander'
        ]
        
        if 'W' in colors:
            removal_searches.extend([
                'Swords to Plowshares',
                'Path to Exile'
            ])
        
        if 'B' in colors:
            removal_searches.extend([
                'Murder',
                'Doom Blade'
            ])
        
        if 'R' in colors:
            removal_searches.extend([
                'Lightning Bolt',
                'Chaos Warp'
            ])
        
        removal_cards = []
        for search in removal_searches:
            cards = card_db.search_cards(search, 2)
            removal_cards.extend(cards)
        
        return removal_cards[:count]
    
    def _get_board_wipes(self, colors: List[str], count: int) -> List[Card]:
        """Get board wipe cards"""
        wipe_searches = ['oracle:"destroy all" legal:commander']
        
        if 'W' in colors:
            wipe_searches.extend(['Wrath of God', 'Day of Judgment'])
        
        if 'B' in colors:
            wipe_searches.append('Damnation')
        
        if 'R' in colors:
            wipe_searches.append('Blasphemous Act')
        
        wipe_cards = []
        for search in wipe_searches:
            cards = card_db.search_cards(search, 2)
            wipe_cards.extend(cards)
        
        return wipe_cards[:count]
    
    def _get_protection(self, colors: List[str], count: int) -> List[Card]:
        """Get protection cards"""
        protection_searches = [
            'Lightning Greaves',
            'Swiftfoot Boots',
            'oracle:"hexproof" legal:commander',
            'oracle:"indestructible" legal:commander'
        ]
        
        if 'U' in colors:
            protection_searches.extend(['Counterspell', 'Negate'])
        
        if 'W' in colors:
            protection_searches.extend(['Teferi\'s Protection', 'Heroic Intervention'])
        
        protection_cards = []
        for search in protection_searches:
            cards = card_db.search_cards(search, 2)
            protection_cards.extend(cards)
        
        return protection_cards[:count]
    
    def _get_threats(self, colors: List[str], commander_analysis: Dict, count: int) -> List[Card]:
        """Get threat/creature cards based on commander themes"""
        threat_searches = ['type:creature legal:commander']
        
        # Add theme-specific threats
        for theme in commander_analysis.get('themes', []):
            if theme == 'artifacts':
                threat_searches.append('type:artifact type:creature')
            elif theme == 'tokens':
                threat_searches.append('oracle:"create" oracle:"token"')
            elif theme == 'graveyard':
                threat_searches.append('oracle:"graveyard"')
        
        threat_cards = []
        for search in threat_searches:
            cards = card_db.search_cards(search, 5)
            threat_cards.extend(cards)
        
        return threat_cards[:count]
    
    def _get_win_conditions(self, colors: List[str], count: int) -> List[Card]:
        """Get win condition cards"""
        win_searches = [
            'oracle:"win the game" legal:commander',
            'oracle:"lose the game" legal:commander',
            'type:creature power>=7 legal:commander'
        ]
        
        win_cards = []
        for search in win_searches:
            cards = card_db.search_cards(search, 3)
            win_cards.extend(cards)
        
        return win_cards[:count]
    
    def _get_tutors(self, colors: List[str], count: int) -> List[Card]:
        """Get tutor cards"""
        tutor_searches = [
            'oracle:"search your library" legal:commander',
            'oracle:"tutor" legal:commander'
        ]
        
        if 'B' in colors:
            tutor_searches.extend(['Demonic Tutor', 'Vampiric Tutor'])
        
        tutor_cards = []
        for search in tutor_searches:
            cards = card_db.search_cards(search, 3)
            tutor_cards.extend(cards)
        
        return tutor_cards[:count]
    
    def _get_combo_pieces(self, colors: List[str], commander_analysis: Dict, count: int) -> List[Card]:
        """Get combo pieces"""
        combo_searches = [
            'oracle:"infinite" legal:commander',
            'oracle:"enters the battlefield" legal:commander'
        ]
        
        combo_cards = []
        for search in combo_searches:
            cards = card_db.search_cards(search, 5)
            combo_cards.extend(cards)
        
        return combo_cards[:count]
    
    def _get_utility_cards(self, colors: List[str], count: int) -> List[Card]:
        """Get utility cards"""
        utility_searches = [
            'oracle:"whenever" legal:commander',
            'oracle:"enter the battlefield" legal:commander'
        ]
        
        utility_cards = []
        for search in utility_searches:
            cards = card_db.search_cards(search, 5)
            utility_cards.extend(cards)
        
        return utility_cards[:count]
    
    def _generate_strategy_summary(self, commander: Card, analysis: Dict, focus: str) -> str:
        """Generate strategy summary"""
        themes = analysis.get('themes', [])
        strategy_type = analysis.get('strategy_type', 'value')
        
        summary = f"This {strategy_type} deck focuses on {commander.name}'s"
        
        if themes:
            theme_str = ', '.join(themes[:3])
            summary += f" {theme_str} synergies"
        else:
            summary += " powerful abilities"
        
        summary += f". The strategy emphasizes {focus} gameplay with a focus on"
        
        if strategy_type == 'aggro':
            summary += " fast, aggressive plays and quick victories."
        elif strategy_type == 'control':
            summary += " long-term advantage and controlling the game state."
        elif strategy_type == 'combo':
            summary += " assembling game-winning combinations."
        else:
            summary += " value generation and incremental advantage."
        
        return summary
    
    def _generate_synergy_notes(self, commander: Card, cards: List[Card]) -> List[str]:
        """Generate synergy analysis"""
        notes = []
        
        # Analyze commander synergies
        commander_text = commander.oracle_text.lower()
        
        if 'artifact' in commander_text:
            artifact_count = sum(1 for card in cards if card.is_artifact)
            if artifact_count > 10:
                notes.append(f"Strong artifact synergy with {artifact_count} artifacts")
        
        if 'creature' in commander_text:
            creature_count = sum(1 for card in cards if card.is_creature)
            notes.append(f"Creature-based strategy with {creature_count} creatures")
        
        # Mana curve analysis
        curve = Counter(min(card.mana_value, 6) for card in cards)
        if curve[2] + curve[3] > len(cards) * 0.4:
            notes.append("Well-balanced mana curve for consistent early plays")
        
        # Color distribution
        total_colors = sum(len(card.colors) for card in cards)
        if total_colors > 0:
            avg_colors = total_colors / len([c for c in cards if c.colors])
            if avg_colors < 1.5:
                notes.append("Focused color requirements for consistent mana")
        
        return notes[:5]  # Limit to 5 notes
    
    def _estimate_power_level(self, cards: List[Card]) -> int:
        """Estimate deck power level 1-10"""
        # Simple heuristic based on card characteristics
        score = 5  # Base score
        
        # High-value cards boost score
        expensive_cards = sum(1 for card in cards if card.price_tcgplayer > 20)
        score += min(expensive_cards // 5, 2)
        
        # Fast mana boosts score
        fast_mana = sum(1 for card in cards if 
                       'Sol Ring' in card.name or 
                       'Mana Crypt' in card.name or
                       'Mana Vault' in card.name)
        score += min(fast_mana, 2)
        
        # Tutors boost score
        tutors = sum(1 for card in cards if 'tutor' in card.oracle_text.lower())
        score += min(tutors // 3, 1)
        
        return min(max(score, 1), 10)
    
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