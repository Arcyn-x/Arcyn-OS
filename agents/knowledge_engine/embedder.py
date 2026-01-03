"""
Embedder module for Knowledge Engine.

Uses LLM Gateway for real embedding generation.
"""

from typing import List, Dict, Any, Optional
import math


class Embedder:
    """
    Embedding generator using LLM Gateway.
    
    Responsibilities:
    - Generate embeddings via LLM Gateway
    - Calculate similarity between embeddings
    - Batch embedding for efficiency
    
    All LLM calls route through the central gateway.
    """
    
    def __init__(self, agent_name: str = "Knowledge"):
        """
        Initialize the embedder.
        
        Args:
            agent_name: Agent identifier for gateway routing
        """
        self.agent_name = agent_name
        self.enabled = True
        self._dimension = 768  # Gemini embedding dimension
    
    def embed(self, text: str, task_id: str = "embed") -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            task_id: Task identifier for tracking
        
        Returns:
            Embedding vector (768 dimensions)
        """
        if not self.enabled:
            return []
        
        try:
            from core.llm_gateway import request_embedding
            
            response = request_embedding(
                agent=self.agent_name,
                task_id=task_id,
                texts=text
            )
            
            if response.success:
                embeddings = response.metadata.get("embeddings", [])
                if embeddings:
                    return embeddings[0]
            
            # Return zero vector on failure
            return [0.0] * self._dimension
            
        except Exception as e:
            # Fail gracefully
            return [0.0] * self._dimension
    
    def embed_batch(self, texts: List[str], task_id: str = "embed_batch") -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            task_id: Task identifier for tracking
        
        Returns:
            List of embedding vectors
        """
        if not self.enabled or not texts:
            return [[0.0] * self._dimension for _ in texts]
        
        try:
            from core.llm_gateway import request_embedding
            
            response = request_embedding(
                agent=self.agent_name,
                task_id=task_id,
                texts=texts
            )
            
            if response.success:
                embeddings = response.metadata.get("embeddings", [])
                # Ensure we have embeddings for all texts
                if len(embeddings) >= len(texts):
                    return embeddings[:len(texts)]
            
            # Return zero vectors on failure
            return [[0.0] * self._dimension for _ in texts]
            
        except Exception:
            return [[0.0] * self._dimension for _ in texts]
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Similarity score between -1 and 1
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        if len(embedding1) != len(embedding2):
            return 0.0
        
        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = math.sqrt(sum(a * a for a in embedding1))
        norm2 = math.sqrt(sum(b * b for b in embedding2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def search_similar(
        self,
        query_embedding: List[float],
        embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find most similar embeddings to query.
        
        Args:
            query_embedding: Query embedding vector
            embeddings: List of embeddings to search
            top_k: Number of top results to return
        
        Returns:
            List of {index, similarity} dicts sorted by similarity
        """
        results = []
        
        for i, emb in enumerate(embeddings):
            sim = self.similarity(query_embedding, emb)
            results.append({"index": i, "similarity": sim})
        
        # Sort by similarity descending
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results[:top_k]
    
    def is_enabled(self) -> bool:
        """Check if embeddings are enabled."""
        return self.enabled
    
    def enable(self) -> None:
        """Enable embeddings."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable embeddings."""
        self.enabled = False
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension
