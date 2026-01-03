"""
Memory Store module for Knowledge Engine.

Stores structured records with namespaces, versioning, and read-only snapshots.
"""

import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import uuid


class MemoryStore:
    """
    Stores structured knowledge records.
    
    Responsibilities:
    - Store structured records
    - Support namespaces (architecture, build, integration, logs)
    - Support versioning
    - Allow read-only snapshots
    
    Uses SQLite backend - no external DBs.
    
    TODO: Add compression for large records
    TODO: Implement record expiration
    TODO: Add backup and restore
    TODO: Implement query optimization
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the memory store.
        
        Args:
            db_path: Path to SQLite database (defaults to ./knowledge/knowledge.db)
        """
        if db_path is None:
            db_path = Path("./knowledge/knowledge.db")
        else:
            db_path = Path(db_path)
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the database schema."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create knowledge table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                namespace TEXT NOT NULL,
                key TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                provenance TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                UNIQUE(namespace, key, version)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_namespace_key 
            ON knowledge(namespace, key)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON knowledge(created_at)
        """)
        
        conn.commit()
        conn.close()
    
    def store(self, namespace: str, key: str, content: Dict[str, Any], 
              provenance: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None,
              version: Optional[int] = None) -> str:
        """
        Store a knowledge record.
        
        Args:
            namespace: Namespace (e.g., "architecture", "build", "integration")
            key: Unique key within namespace
            content: Content to store (must be JSON-serializable)
            provenance: Provenance metadata
            metadata: Optional additional metadata
            version: Optional version number (auto-increments if not provided)
        
        Returns:
            Record ID
        """
        record_id = str(uuid.uuid4())
        
        # Get next version if not provided
        if version is None:
            version = self._get_next_version(namespace, key)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO knowledge 
                (id, namespace, key, content, metadata, provenance, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id,
                namespace,
                key,
                json.dumps(content),
                json.dumps(metadata) if metadata else None,
                json.dumps(provenance),
                version,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            return record_id
            
        finally:
            conn.close()
    
    def retrieve(self, namespace: str, key: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a knowledge record.
        
        Args:
            namespace: Namespace
            key: Key
            version: Optional version (returns latest if not provided)
        
        Returns:
            Record dictionary or None if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if version:
                cursor.execute("""
                    SELECT * FROM knowledge 
                    WHERE namespace = ? AND key = ? AND version = ?
                """, (namespace, key, version))
            else:
                cursor.execute("""
                    SELECT * FROM knowledge 
                    WHERE namespace = ? AND key = ?
                    ORDER BY version DESC
                    LIMIT 1
                """, (namespace, key))
            
            row = cursor.fetchone()
            
            if row:
                return {
                    "id": row["id"],
                    "namespace": row["namespace"],
                    "key": row["key"],
                    "content": json.loads(row["content"]),
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                    "provenance": json.loads(row["provenance"]),
                    "version": row["version"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
            
            return None
            
        finally:
            conn.close()
    
    def search(self, namespace: Optional[str] = None, filters: Optional[Dict[str, Any]] = None,
               limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search knowledge records.
        
        Args:
            namespace: Optional namespace filter
            filters: Optional additional filters
            limit: Maximum number of results
        
        Returns:
            List of matching records
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM knowledge WHERE 1=1"
            params = []
            
            if namespace:
                query += " AND namespace = ?"
                params.append(namespace)
            
            if filters:
                # Simple filter support (can be extended)
                if "source_agent" in filters:
                    query += " AND provenance LIKE ?"
                    params.append(f'%"source_agent":"{filters["source_agent"]}"%')
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "namespace": row["namespace"],
                    "key": row["key"],
                    "content": json.loads(row["content"]),
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                    "provenance": json.loads(row["provenance"]),
                    "version": row["version"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                })
            
            return results
            
        finally:
            conn.close()
    
    def _get_next_version(self, namespace: str, key: str) -> int:
        """
        Get the next version number for a key.
        
        Args:
            namespace: Namespace
            key: Key
        
        Returns:
            Next version number
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT MAX(version) FROM knowledge 
                WHERE namespace = ? AND key = ?
            """, (namespace, key))
            
            result = cursor.fetchone()
            if result and result[0]:
                return result[0] + 1
            
            return 1
            
        finally:
            conn.close()
    
    def get_namespaces(self) -> List[str]:
        """
        Get list of all namespaces.
        
        Returns:
            List of namespace names
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT DISTINCT namespace FROM knowledge")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_keys(self, namespace: str) -> List[str]:
        """
        Get list of all keys in a namespace.
        
        Args:
            namespace: Namespace
        
        Returns:
            List of key names
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT key FROM knowledge 
                WHERE namespace = ?
            """, (namespace,))
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def delete(self, namespace: str, key: str, version: Optional[int] = None) -> bool:
        """
        Delete a knowledge record.
        
        Args:
            namespace: Namespace
            key: Key
            version: Optional version (deletes all versions if not provided)
        
        Returns:
            True if deleted, False otherwise
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            if version:
                cursor.execute("""
                    DELETE FROM knowledge 
                    WHERE namespace = ? AND key = ? AND version = ?
                """, (namespace, key, version))
            else:
                cursor.execute("""
                    DELETE FROM knowledge 
                    WHERE namespace = ? AND key = ?
                """, (namespace, key))
            
            conn.commit()
            return cursor.rowcount > 0
            
        finally:
            conn.close()
    
    def create_snapshot(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a read-only snapshot of the knowledge store.
        
        Args:
            namespace: Optional namespace to snapshot (all if None)
        
        Returns:
            Snapshot dictionary
        """
        snapshot = {
            "snapshot_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "namespace": namespace,
            "records": []
        }
        
        records = self.search(namespace=namespace, limit=10000)
        snapshot["records"] = records
        snapshot["record_count"] = len(records)
        
        return snapshot

