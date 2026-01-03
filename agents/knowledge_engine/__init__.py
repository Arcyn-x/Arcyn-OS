"""
Knowledge Engine (S-2) for Arcyn OS.

The Knowledge Engine is responsible for:
- Structured memory
- Knowledge retrieval
- Context grounding
- Preventing hallucinations

It is not a chat agent and does not make decisions.
"""

from .knowledge_engine import KnowledgeEngine
from .memory_store import MemoryStore
from .retriever import Retriever
from .embedder import Embedder
from .provenance import Provenance

__all__ = ['KnowledgeEngine', 'MemoryStore', 'Retriever', 'Embedder', 'Provenance']

