"""
Retriever module for Knowledge Engine.

Keyword-based retrieval with metadata filtering and ranking.
"""

from typing import Dict, Any, List, Optional, Tuple
import json
import re
from datetime import datetime


class Retriever:
    """
    Retrieves knowledge based on queries.
    
    Responsibilities:
    - Keyword-based retrieval (v1)
    - Metadata filtering
    - Ranking logic
    
    LLM or vector search hooks should be TODOs only.
    
    TODO: Add vector similarity search
    TODO: Implement semantic search with LLM
    TODO: Add query expansion
    TODO: Implement advanced ranking algorithms
    """
    
    def __init__(self, memory_store: Any):
        """
        Initialize the retriever.
        
        Args:
            memory_store: MemoryStore instance
        """
        self.memory_store = memory_store
    
    def retrieve(self, query: str, namespace: Optional[str] = None,
                 filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve knowledge matching a query.
        
        Args:
            query: Search query (keywords)
            namespace: Optional namespace filter
            filters: Optional metadata filters
            limit: Maximum number of results
        
        Returns:
            List of matching records with confidence scores
        """
        # Get all records from namespace
        all_records = self.memory_store.search(namespace=namespace, filters=filters, limit=1000)
        
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        
        if not keywords:
            return []
        
        # Score and rank records
        scored_records = []
        for record in all_records:
            score = self._score_record(record, keywords)
            if score > 0:
                scored_records.append({
                    "record": record,
                    "score": score,
                    "confidence": min(1.0, score / len(keywords))
                })
        
        # Sort by score (descending)
        scored_records.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top results
        return scored_records[:limit]
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from query.
        
        Args:
            query: Search query
        
        Returns:
            List of keywords
        """
        # Simple keyword extraction (lowercase, split on whitespace)
        keywords = re.findall(r'\b\w+\b', query.lower())
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [kw for kw in keywords if kw not in stop_words and len(kw) > 2]
        return keywords
    
    def _score_record(self, record: Dict[str, Any], keywords: List[str]) -> float:
        """
        Score a record against keywords.
        
        Args:
            record: Knowledge record
            keywords: List of keywords
        
        Returns:
            Score (higher is better)
        """
        score = 0.0
        content = record.get("content", {})
        
        # Convert content to searchable text
        searchable_text = self._extract_searchable_text(content)
        searchable_text_lower = searchable_text.lower()
        
        # Score based on keyword matches
        for keyword in keywords:
            # Count occurrences
            count = searchable_text_lower.count(keyword.lower())
            score += count * 1.0
            
            # Bonus for exact phrase matches
            if keyword in searchable_text_lower:
                score += 2.0
        
        # Check metadata
        metadata = record.get("metadata", {})
        if metadata:
            metadata_text = json.dumps(metadata).lower()
            for keyword in keywords:
                if keyword in metadata_text:
                    score += 0.5
        
        # Check key and namespace
        key = record.get("key", "").lower()
        namespace = record.get("namespace", "").lower()
        for keyword in keywords:
            if keyword in key:
                score += 1.5
            if keyword in namespace:
                score += 1.0
        
        return score
    
    def _extract_searchable_text(self, content: Any) -> str:
        """
        Extract searchable text from content.
        
        Args:
            content: Content (dict, list, or string)
        
        Returns:
            Searchable text string
        """
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            # Recursively extract text from dict
            texts = []
            for key, value in content.items():
                texts.append(str(key))
                texts.append(self._extract_searchable_text(value))
            return " ".join(texts)
        elif isinstance(content, list):
            return " ".join(self._extract_searchable_text(item) for item in content)
        else:
            return str(content)
    
    def retrieve_by_provenance(self, source_agent: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve records by source agent.
        
        Args:
            source_agent: Source agent name
            limit: Maximum number of results
        
        Returns:
            List of records from the specified agent
        """
        filters = {"source_agent": source_agent}
        records = self.memory_store.search(filters=filters, limit=limit)
        
        return [{"record": r, "score": 1.0, "confidence": 1.0} for r in records]
    
    def retrieve_recent(self, namespace: Optional[str] = None, days: int = 7, 
                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent records.
        
        Args:
            namespace: Optional namespace filter
            days: Number of days to look back
            limit: Maximum number of results
        
        Returns:
            List of recent records
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        all_records = self.memory_store.search(namespace=namespace, limit=1000)
        recent_records = []
        
        for record in all_records:
            created_at = record.get("created_at", "")
            try:
                record_time = datetime.fromisoformat(created_at).timestamp()
                if record_time >= cutoff_date:
                    recent_records.append({
                        "record": record,
                        "score": 1.0,
                        "confidence": 1.0
                    })
            except (ValueError, TypeError):
                continue
        
        # Sort by created_at (newest first)
        recent_records.sort(key=lambda x: x["record"].get("created_at", ""), reverse=True)
        
        return recent_records[:limit]

