# ai-workflow-fastapi/services/__init__.py

"""
AI Workflow Services Package

This package contains intelligent services for the AI deck builder:
- card_database: Interface to Django backend card database
- recommendation_engine: Intelligent card recommendation system
"""

from .card_database import card_db, Card
from .recommendation_engine import recommendation_engine

__all__ = ['card_db', 'Card', 'recommendation_engine']