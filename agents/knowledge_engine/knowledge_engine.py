"""
Knowledge Engine (S-2) for Arcyn OS.

The Knowledge Engine is responsible for structured memory, knowledge retrieval,
context grounding, and preventing hallucinations.
"""

from typing import Dict, Any, List, Optional
from .memory_store import MemoryStore
from .retriever import Retriever
from .embedder import Embedder
from .provenance import Provenance
from core.logger import Logger
from core.context_manager import ContextManager
from core.memory import Memory


class KnowledgeEngine:
    """
    Main Knowledge Engine class.
    
    The Knowledge Engine is not a chat agent and does not make decisions.
    It is read-first, write-controlled.
    
    Example:
        >>> engine = KnowledgeEngine()
        >>> result = engine.ingest({
        ...     "namespace": "architecture",
        ...     "key": "design_001",
        ...     "content": {...},
        ...     "source_agent": "system_designer"
        ... })
        >>> results = engine.query("memory system")
    """
    
    def __init__(self, agent_id: str = "knowledge_engine", log_level: int = 20, db_path: Optional[str] = None):
        """
        Initialize the Knowledge Engine.
        
        Args:
            agent_id: Unique identifier for this agent instance
            log_level: Logging level (default: 20 = INFO)
            db_path: Optional path to knowledge database
        """
        self.agent_id = agent_id
        self.logger = Logger(f"KnowledgeEngine-{agent_id}", log_level=log_level)
        self.context = ContextManager(agent_id)
        self.memory = Memory()
        
        # Initialize sub-components
        self.memory_store = MemoryStore(db_path=db_path)
        self.retriever = Retriever(self.memory_store)
        self.embedder = Embedder()
        
        self.logger.info(f"Knowledge Engine {agent_id} initialized")
        self.context.set_state('idle')
    
    def ingest(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest knowledge from a source.
        
        Args:
            source: Source dictionary with:
                - namespace: Namespace (e.g., "architecture", "build")
                - key: Unique key
                - content: Content to store
                - source_agent: Source agent name
                - metadata: Optional metadata
                - version: Optional version
        
        Returns:
            Dictionary containing:
            {
                "success": bool,
                "record_id": str or None,
                "error": str or None
            }
        """
        self.logger.info(f"Ingesting knowledge: {source.get('namespace')}/{source.get('key')}")
        self.context.set_state('ingesting')
        self.context.add_history('ingest_started', {'namespace': source.get('namespace'), 'key': source.get('key')})
        
        result = {
            "success": False,
            "record_id": None,
            "error": None
        }
        
        try:
            # Validate required fields
            required = ["namespace", "key", "content", "source_agent"]
            missing = [field for field in required if field not in source]
            
            if missing:
                result["error"] = f"Missing required fields: {', '.join(missing)}"
                self.context.set_state('error')
                return result
            
            # Create provenance
            provenance_obj = Provenance(
                source_agent=source["source_agent"],
                source_version=source.get("source_version")
            )
            provenance = provenance_obj.create(source.get("provenance_metadata"))
            
            # Store knowledge
            record_id = self.memory_store.store(
                namespace=source["namespace"],
                key=source["key"],
                content=source["content"],
                provenance=provenance,
                metadata=source.get("metadata"),
                version=source.get("version")
            )
            
            result["success"] = True
            result["record_id"] = record_id
            
            self.context.add_history('ingest_completed', {'record_id': record_id})
            self.context.set_state('idle')
            
            self.logger.info(f"Knowledge ingested: {record_id}")
            return result
            
        except Exception as e:
            error_msg = f"Error ingesting knowledge: {str(e)}"
            self.logger.error(error_msg)
            result["error"] = error_msg
            self.context.set_state('error')
            self.context.add_history('ingest_failed', {'error': str(e)})
            return result
    
    def query(self, query: str, filters: Optional[Dict[str, Any]] = None, 
              namespace: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Query knowledge store.
        
        Args:
            query: Search query
            filters: Optional metadata filters
            namespace: Optional namespace filter
            limit: Maximum number of results
        
        Returns:
            Dictionary containing:
            {
                "matched_entries": List[Dict],
                "confidence_scores": List[float],
                "provenance_metadata": List[Dict],
                "count": int
            }
        """
        self.logger.info(f"Querying knowledge: {query[:50]}...")
        self.context.set_state('querying')
        self.context.add_history('query_started', {'query': query})
        
        result = {
            "matched_entries": [],
            "confidence_scores": [],
            "provenance_metadata": [],
            "count": 0
        }
        
        try:
            # Retrieve matching records
            matches = self.retriever.retrieve(
                query=query,
                namespace=namespace,
                filters=filters,
                limit=limit
            )
            
            if not matches:
                self.logger.info("No matches found")
                self.context.set_state('idle')
                return result
            
            # Extract results
            for match in matches:
                record = match["record"]
                result["matched_entries"].append(record["content"])
                result["confidence_scores"].append(match["confidence"])
                result["provenance_metadata"].append(record["provenance"])
            
            result["count"] = len(matches)
            
            self.context.add_history('query_completed', {'count': result["count"]})
            self.context.set_state('idle')
            
            self.logger.info(f"Query completed: {result['count']} matches")
            return result
            
        except Exception as e:
            error_msg = f"Error querying knowledge: {str(e)}"
            self.logger.error(error_msg)
            self.context.set_state('error')
            self.context.add_history('query_failed', {'error': str(e)})
            return result
    
    def summarize(self, scope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize knowledge within a scope.
        
        Args:
            scope: Scope dictionary with:
                - namespace: Optional namespace
                - source_agent: Optional source agent filter
                - time_range: Optional time range (days)
        
        Returns:
            Dictionary containing:
            {
                "summary": Dict,
                "record_count": int,
                "namespaces": List[str],
                "provenance_summary": Dict
            }
        """
        self.logger.info("Summarizing knowledge")
        self.context.set_state('summarizing')
        self.context.add_history('summarize_started', {'scope': scope})
        
        result = {
            "summary": {},
            "record_count": 0,
            "namespaces": [],
            "provenance_summary": {}
        }
        
        try:
            namespace = scope.get("namespace")
            source_agent = scope.get("source_agent")
            time_range = scope.get("time_range", 30)  # days
            
            # Get namespaces
            if namespace:
                result["namespaces"] = [namespace]
            else:
                result["namespaces"] = self.memory_store.get_namespaces()
            
            # Get records
            filters = {}
            if source_agent:
                filters["source_agent"] = source_agent
            
            records = self.memory_store.search(namespace=namespace, filters=filters, limit=10000)
            result["record_count"] = len(records)
            
            # Build summary by namespace
            summary_by_namespace = {}
            provenance_counts = {}
            
            for record in records:
                ns = record["namespace"]
                if ns not in summary_by_namespace:
                    summary_by_namespace[ns] = {"count": 0, "keys": set()}
                summary_by_namespace[ns]["count"] += 1
                summary_by_namespace[ns]["keys"].add(record["key"])
                
                # Count by provenance
                prov = record.get("provenance", {})
                agent = prov.get("source_agent", "unknown")
                provenance_counts[agent] = provenance_counts.get(agent, 0) + 1
            
            # Convert sets to lists for JSON serialization
            for ns_data in summary_by_namespace.values():
                ns_data["keys"] = list(ns_data["keys"])
            
            result["summary"] = summary_by_namespace
            result["provenance_summary"] = provenance_counts
            
            self.context.add_history('summarize_completed', {'record_count': result["record_count"]})
            self.context.set_state('idle')
            
            self.logger.info(f"Summary completed: {result['record_count']} records")
            return result
            
        except Exception as e:
            error_msg = f"Error summarizing knowledge: {str(e)}"
            self.logger.error(error_msg)
            self.context.set_state('error')
            self.context.add_history('summarize_failed', {'error': str(e)})
            return result
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current engine status.
        
        Returns:
            Dictionary with engine status and statistics
        """
        namespaces = self.memory_store.get_namespaces()
        total_records = sum(
            len(self.memory_store.get_keys(ns)) for ns in namespaces
        )
        
        return {
            "agent_id": self.agent_id,
            "state": self.context.get_state(),
            "namespaces": namespaces,
            "total_records": total_records,
            "embeddings_enabled": self.embedder.is_enabled()
        }

