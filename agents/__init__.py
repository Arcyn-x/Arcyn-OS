"""
Agents package for Arcyn OS.

This package contains all agent implementations.

Available Agents:
    - PersonaAgent (S-1): Human interface — intent classification & routing
    - ArchitectAgent (A-1): Plans and structures development tasks
    - BuilderAgent (F-1): Implements code from plans
    - SystemDesignerAgent (F-2): Architectural validation & standards
    - IntegratorAgent (F-3): Compatibility, dependency, standards enforcement
    - KnowledgeEngine (S-2): Persistent memory, embeddings, retrieval
    - EvolutionAgent (S-3): System monitoring & improvement advisory
"""

from .persona import PersonaAgent
from .architect import ArchitectAgent
from .builder import BuilderAgent
from .system_designer import SystemDesignerAgent
from .integrator import IntegratorAgent
from .knowledge_engine import KnowledgeEngine
from .evolution import EvolutionAgent

__all__ = [
    'PersonaAgent',
    'ArchitectAgent',
    'BuilderAgent',
    'SystemDesignerAgent',
    'IntegratorAgent',
    'KnowledgeEngine',
    'EvolutionAgent',
]

