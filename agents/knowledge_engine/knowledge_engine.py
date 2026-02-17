"""
Knowledge Engine (S-2) for Arcyn OS.

The Knowledge Engine is responsible for structured memory, knowledge retrieval,
context grounding, and preventing hallucinations.

Supports both keyword-based and semantic (embedding) search.
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

    Capabilities:
    - ingest: Store structured knowledge with provenance
    - ingest_with_embedding: Store knowledge + generate vector embedding
    - query: Keyword-based retrieval
    - semantic_search: Embedding-based similarity search
    - cross_project_learn: Extract patterns from source code
    - summarize: Aggregate knowledge within a scope

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

        # In-memory vector index: record_id -> embedding vector
        self._embedding_index: Dict[str, List[float]] = {}
        # Reverse lookup: record_id -> {namespace, key, content_preview}
        self._embedding_metadata: Dict[str, Dict[str, Any]] = {}

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

    def ingest_with_embedding(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest knowledge and generate a vector embedding for semantic search.

        This extends `ingest()` by also computing an embedding vector from
        the content and storing it in the in-memory vector index.

        Args:
            source: Same as ingest(), plus optional:
                - embed_text: Custom text to embed (defaults to content string)

        Returns:
            Dictionary containing:
            {
                "success": bool,
                "record_id": str or None,
                "embedded": bool,
                "error": str or None
            }
        """
        # First do the standard ingest
        result = self.ingest(source)

        if not result["success"]:
            result["embedded"] = False
            return result

        record_id = result["record_id"]

        # Generate embedding
        try:
            content = source.get("content", {})
            embed_text = source.get("embed_text")
            if not embed_text:
                # Convert content to text for embedding
                if isinstance(content, dict):
                    import json
                    embed_text = json.dumps(content, default=str)
                elif isinstance(content, str):
                    embed_text = content
                else:
                    embed_text = str(content)

            # Truncate to avoid excessive token usage
            embed_text = embed_text[:10000]

            embedding = self.embedder.embed(embed_text, task_id="ingest_embed")

            if embedding and any(v != 0.0 for v in embedding):
                self._embedding_index[record_id] = embedding
                self._embedding_metadata[record_id] = {
                    "namespace": source.get("namespace"),
                    "key": source.get("key"),
                    "content_preview": embed_text[:200],
                    "source_agent": source.get("source_agent")
                }
                result["embedded"] = True
                self.logger.info(f"Embedding generated for {record_id}")
            else:
                result["embedded"] = False
                self.logger.warning(f"Zero embedding returned for {record_id}")

        except Exception as e:
            result["embedded"] = False
            self.logger.warning(f"Embedding generation failed: {str(e)}")

        return result

    def query(self, query: str, filters: Optional[Dict[str, Any]] = None,
              namespace: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Query knowledge store (keyword-based).

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

    def semantic_search(
        self,
        query: str,
        namespace: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        Search knowledge using embedding similarity.

        Embeds the query and compares against the vector index to find
        semantically similar knowledge entries.

        Args:
            query: Natural language search query
            namespace: Optional namespace filter
            top_k: Maximum results to return
            threshold: Minimum cosine similarity (0.0 to 1.0)

        Returns:
            Dictionary containing:
            {
                "results": List[Dict],  # {record_id, similarity, metadata}
                "count": int,
                "query_embedded": bool
            }
        """
        self.logger.info(f"Semantic search: {query[:50]}...")
        self.context.set_state('searching')

        result: Dict[str, Any] = {
            "results": [],
            "count": 0,
            "query_embedded": False
        }

        if not self._embedding_index:
            self.logger.info("No embeddings in index - falling back to empty result")
            self.context.set_state('idle')
            return result

        try:
            # Embed the query
            query_embedding = self.embedder.embed(query, task_id="semantic_search")

            if not query_embedding or all(v == 0.0 for v in query_embedding):
                self.logger.warning("Failed to embed query")
                self.context.set_state('idle')
                return result

            result["query_embedded"] = True

            # Score all indexed embeddings
            candidates = list(self._embedding_index.keys())
            embeddings = [self._embedding_index[rid] for rid in candidates]

            similarities = self.embedder.search_similar(
                query_embedding=query_embedding,
                embeddings=embeddings,
                top_k=len(candidates)  # score all, then filter
            )

            # Filter by threshold and namespace
            for sim_result in similarities:
                idx = sim_result["index"]
                score = sim_result["similarity"]

                if score < threshold:
                    continue

                record_id = candidates[idx]
                meta = self._embedding_metadata.get(record_id, {})

                # Apply namespace filter
                if namespace and meta.get("namespace") != namespace:
                    continue

                result["results"].append({
                    "record_id": record_id,
                    "similarity": round(score, 4),
                    "namespace": meta.get("namespace"),
                    "key": meta.get("key"),
                    "content_preview": meta.get("content_preview", ""),
                    "source_agent": meta.get("source_agent")
                })

                if len(result["results"]) >= top_k:
                    break

            result["count"] = len(result["results"])

            self.context.add_history('semantic_search_completed', {
                'count': result["count"],
                'threshold': threshold
            })
            self.context.set_state('idle')

            self.logger.info(f"Semantic search: {result['count']} results above threshold {threshold}")
            return result

        except Exception as e:
            error_msg = f"Error in semantic search: {str(e)}"
            self.logger.error(error_msg)
            self.context.set_state('error')
            return result

    def cross_project_learn(
        self,
        source_files: List[str],
        project_name: str,
        source_agent: str = "Knowledge"
    ) -> Dict[str, Any]:
        """
        Extract patterns and knowledge from source code files for cross-project learning.

        Analyzes source files, extracts structural patterns (classes, functions,
        imports), and ingests them as searchable knowledge with embeddings.

        Args:
            source_files: List of file paths to learn from
            project_name: Name of the source project
            source_agent: Agent performing the learning

        Returns:
            Dictionary with learning summary:
            {
                "success": bool,
                "files_processed": int,
                "patterns_extracted": int,
                "errors": List[str]
            }
        """
        import ast as _ast

        self.logger.info(f"Cross-project learning from {project_name}: {len(source_files)} files")
        self.context.set_state('learning')

        result = {
            "success": False,
            "files_processed": 0,
            "patterns_extracted": 0,
            "errors": []
        }

        for file_path in source_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                tree = _ast.parse(content, filename=file_path)

                # Collect patterns
                patterns = []

                for node in _ast.iter_child_nodes(tree):
                    if isinstance(node, _ast.ClassDef):
                        methods = [
                            m.name for m in node.body
                            if isinstance(m, (_ast.FunctionDef, _ast.AsyncFunctionDef))
                        ]
                        pattern = {
                            "type": "class",
                            "name": node.name,
                            "bases": [self._ast_name(b) for b in node.bases],
                            "methods": methods,
                            "line_count": (node.end_lineno or node.lineno) - node.lineno + 1,
                            "docstring": _ast.get_docstring(node)
                        }
                        patterns.append(pattern)

                    elif isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                        pattern = {
                            "type": "function",
                            "name": node.name,
                            "args": [a.arg for a in node.args.args],
                            "is_async": isinstance(node, _ast.AsyncFunctionDef),
                            "docstring": _ast.get_docstring(node)
                        }
                        patterns.append(pattern)

                if patterns:
                    import json as _json

                    ingest_result = self.ingest_with_embedding({
                        "namespace": f"learned:{project_name}",
                        "key": file_path,
                        "content": {"file": file_path, "patterns": patterns},
                        "source_agent": source_agent,
                        "embed_text": _json.dumps(patterns, default=str),
                        "metadata": {
                            "project": project_name,
                            "pattern_count": len(patterns)
                        }
                    })

                    if ingest_result["success"]:
                        result["patterns_extracted"] += len(patterns)

                result["files_processed"] += 1

            except SyntaxError:
                result["errors"].append(f"Parse error: {file_path}")
            except IOError:
                result["errors"].append(f"Read error: {file_path}")
            except Exception as e:
                result["errors"].append(f"Error processing {file_path}: {str(e)}")

        result["success"] = result["files_processed"] > 0

        self.context.add_history('cross_project_learn_completed', {
            'project': project_name,
            'files': result["files_processed"],
            'patterns': result["patterns_extracted"]
        })
        self.context.set_state('idle')

        self.logger.info(
            f"Cross-project learning complete: {result['files_processed']} files, "
            f"{result['patterns_extracted']} patterns"
        )
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
            "embeddings_enabled": self.embedder.is_enabled(),
            "indexed_embeddings": len(self._embedding_index)
        }

    # --- Helpers ---

    @staticmethod
    def _ast_name(node) -> str:
        """Extract name from an AST node."""
        import ast as _ast
        if isinstance(node, _ast.Name):
            return node.id
        elif isinstance(node, _ast.Attribute):
            return f"{KnowledgeEngine._ast_name(node.value)}.{node.attr}"
        return "<unknown>"
