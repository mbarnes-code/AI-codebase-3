# ai-workflow-fastapi/services/__init__.py

"""
AI Workflow Services Package

This package contains intelligent services for the AI deck builder:
- card_database: Interface to Django backend card database
- combo_database: Interface to Django backend combo/variant database  
- recommendation_engine: Enhanced intelligent card recommendation system with combo detection
"""

from .card_database import card_db, Card
from .combo_database import combo_db, Combo, Variant
from .recommendation_engine import recommendation_engine

__all__ = ['card_db', 'Card', 'combo_db', 'Combo', 'Variant', 'recommendation_engine']