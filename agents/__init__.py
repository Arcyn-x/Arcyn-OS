"""
Agents package for Arcyn OS.

This package contains all agent implementations.

Available Agents:
    - ArchitectAgent (A-1): Plans and structures development tasks
    - BuilderAgent (B-1): Implements code from plans
    - IntegratorAgent (I-1): Integrates components
    - KnowledgeEngineAgent (K-1): Manages knowledge base
    - PersonaAgent (P-1): Handles user interactions
    - SystemDesignerAgent (D-1): Designs system architecture
    - EvolutionAgent (S-3): Monitors, analyzes, recommends improvements
"""

# Evolution Agent (S-3) - Advisory-only system monitor
from .evolution import EvolutionAgent

__all__ = [
    'EvolutionAgent',
]

