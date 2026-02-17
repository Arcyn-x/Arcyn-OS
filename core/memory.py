"""
Memory module for Arcyn OS.

Provides persistent storage and retrieval of agent state, plans, and context.

Storage Backends:
    - In-memory cache (fast reads)
    - JSON files (human-readable persistence)
    - SQLite database (structured queries, metadata)

Features:
    - Read-through cache with JSON file + SQLite backing
    - Metadata tracking (timestamps, access counts, agent source)
    - Namespace support for agent isolation
    - Search by key pattern or metadata
    - Auto-cleanup of expired entries
"""

import json
import sqlite3
import time
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime


class Memory:
    """
    Memory manager for storing and retrieving agent data.

    Provides a read-through cache backed by JSON files and an optional
    SQLite database for metadata, search, and structured queries.

    Example:
        >>> mem = Memory("./memory")
        >>> mem.write("plan_001", {"goal": "Build API"}, namespace="architect")
        True
        >>> mem.read("plan_001")
        {"goal": "Build API"}
        >>> mem.search("plan")
        [{"key": "plan_001", ...}]
    """

    def __init__(self, storage_path: Optional[str] = None, enable_db: bool = True):
        """
        Initialize the memory manager.

        Args:
            storage_path: Path to storage directory. Defaults to ./memory/
            enable_db: Whether to enable SQLite metadata database
        """
        self.storage_path = Path(storage_path) if storage_path else Path("./memory")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Any] = {}
        self._db_enabled = enable_db
        self._db: Optional[sqlite3.Connection] = None
        self.logger = logging.getLogger("arcyn.memory")

        if self._db_enabled:
            self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite metadata database."""
        try:
            db_path = self.storage_path / "memory_index.db"
            self._db = sqlite3.connect(str(db_path), check_same_thread=False)
            self._db.row_factory = sqlite3.Row
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    key TEXT PRIMARY KEY,
                    namespace TEXT DEFAULT 'default',
                    source_agent TEXT DEFAULT 'unknown',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    accessed_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    size_bytes INTEGER DEFAULT 0,
                    data_type TEXT DEFAULT 'json',
                    tags TEXT DEFAULT '[]',
                    ttl_seconds INTEGER DEFAULT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            self._db.execute("""
                CREATE INDEX IF NOT EXISTS idx_namespace ON memory_entries(namespace)
            """)
            self._db.execute("""
                CREATE INDEX IF NOT EXISTS idx_source_agent ON memory_entries(source_agent)
            """)
            self._db.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON memory_entries(created_at)
            """)
            self._db.commit()
        except Exception as e:
            self.logger.warning(f"SQLite init failed, falling back to file-only: {e}")
            self._db_enabled = False
            self._db = None

    def write(self, key: str, data: Any, namespace: str = "default",
              source_agent: str = "unknown", tags: Optional[List[str]] = None,
              ttl_seconds: Optional[int] = None,
              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Write data to memory with full metadata.

        Args:
            key: Unique identifier for the data
            data: Data to store (must be JSON serializable)
            namespace: Namespace for agent isolation (e.g., "architect", "builder")
            source_agent: ID of the agent writing the data
            tags: Optional tags for categorization
            ttl_seconds: Optional time-to-live in seconds
            metadata: Optional additional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            # Store in cache
            self._cache[key] = data

            # Write JSON file
            file_path = self.storage_path / f"{key}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            # Update SQLite index
            if self._db:
                now = datetime.now().isoformat()
                serialized_data = json.dumps(data, default=str)
                self._db.execute("""
                    INSERT INTO memory_entries
                        (key, namespace, source_agent, created_at, updated_at,
                         accessed_at, access_count, size_bytes, tags, ttl_seconds, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        updated_at = ?,
                        accessed_at = ?,
                        size_bytes = ?,
                        tags = ?,
                        metadata = ?
                """, (
                    key, namespace, source_agent, now, now, now,
                    len(serialized_data),
                    json.dumps(tags or []),
                    ttl_seconds,
                    json.dumps(metadata or {}),
                    # ON CONFLICT params
                    now, now,
                    len(serialized_data),
                    json.dumps(tags or []),
                    json.dumps(metadata or {}),
                ))
                self._db.commit()

            return True

        except Exception as e:
            self.logger.error(f"Memory write failed for key '{key}': {e}")
            return False

    def read(self, key: str) -> Optional[Any]:
        """
        Read data from memory.

        Uses cache-first strategy, falling back to disk.

        Args:
            key: Unique identifier for the data

        Returns:
            Stored data if found, None otherwise
        """
        # Check cache first
        if key in self._cache:
            self._touch(key)
            return self._cache[key]

        # Load from disk
        file_path = self.storage_path / f"{key}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache[key] = data
                    self._touch(key)
                    return data
            except Exception as e:
                self.logger.error(f"Memory read failed for key '{key}': {e}")
                return None

        return None

    def delete(self, key: str) -> bool:
        """
        Delete data from memory (cache, file, and DB).

        Args:
            key: Unique identifier for the data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from cache
            self._cache.pop(key, None)

            # Remove file
            file_path = self.storage_path / f"{key}.json"
            if file_path.exists():
                file_path.unlink()

            # Remove from DB
            if self._db:
                self._db.execute("DELETE FROM memory_entries WHERE key = ?", (key,))
                self._db.commit()

            return True
        except Exception as e:
            self.logger.error(f"Memory delete failed for key '{key}': {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if data exists in memory.

        Args:
            key: Unique identifier for the data

        Returns:
            True if data exists, False otherwise
        """
        if key in self._cache:
            return True
        file_path = self.storage_path / f"{key}.json"
        return file_path.exists()

    def search(self, pattern: str, namespace: Optional[str] = None,
               limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search memory entries by key pattern or namespace.

        Args:
            pattern: Key pattern to search (SQL LIKE pattern)
            namespace: Optional namespace filter
            limit: Maximum results to return

        Returns:
            List of matching entry metadata dictionaries
        """
        results = []

        if self._db:
            try:
                query = "SELECT * FROM memory_entries WHERE key LIKE ?"
                params: list = [f"%{pattern}%"]

                if namespace:
                    query += " AND namespace = ?"
                    params.append(namespace)

                query += " ORDER BY updated_at DESC LIMIT ?"
                params.append(limit)

                cursor = self._db.execute(query, params)
                for row in cursor:
                    results.append(dict(row))

            except Exception as e:
                self.logger.error(f"Memory search failed: {e}")
        else:
            # Fallback: search files
            for file_path in self.storage_path.glob("*.json"):
                if pattern.lower() in file_path.stem.lower():
                    results.append({
                        "key": file_path.stem,
                        "size_bytes": file_path.stat().st_size,
                        "updated_at": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                    })
                    if len(results) >= limit:
                        break

        return results

    def list_keys(self, namespace: Optional[str] = None) -> List[str]:
        """
        List all keys in memory.

        Args:
            namespace: Optional namespace filter

        Returns:
            List of key strings
        """
        if self._db and namespace:
            try:
                cursor = self._db.execute(
                    "SELECT key FROM memory_entries WHERE namespace = ?",
                    (namespace,)
                )
                return [row['key'] for row in cursor]
            except Exception:
                pass

        # Fallback: list files
        return [f.stem for f in self.storage_path.glob("*.json")]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.

        Returns:
            Dictionary with entry count, size, and namespace breakdown
        """
        stats: Dict[str, Any] = {
            "cache_entries": len(self._cache),
            "file_entries": len(list(self.storage_path.glob("*.json"))),
            "db_enabled": self._db_enabled,
        }

        if self._db:
            try:
                cursor = self._db.execute(
                    "SELECT COUNT(*) as count, SUM(size_bytes) as total_bytes, "
                    "namespace FROM memory_entries GROUP BY namespace"
                )
                namespaces = {}
                total_entries = 0
                total_bytes = 0
                for row in cursor:
                    namespaces[row['namespace']] = {
                        "count": row['count'],
                        "bytes": row['total_bytes'] or 0,
                    }
                    total_entries += row['count']
                    total_bytes += (row['total_bytes'] or 0)

                stats["total_entries"] = total_entries
                stats["total_bytes"] = total_bytes
                stats["namespaces"] = namespaces
            except Exception:
                pass

        return stats

    def _touch(self, key: str) -> None:
        """Update access metadata for a key."""
        if self._db:
            try:
                self._db.execute("""
                    UPDATE memory_entries
                    SET accessed_at = ?, access_count = access_count + 1
                    WHERE key = ?
                """, (datetime.now().isoformat(), key))
                self._db.commit()
            except Exception:
                pass

    def cleanup_expired(self) -> int:
        """
        Remove expired entries (those past their TTL).

        Returns:
            Number of entries removed
        """
        removed = 0
        if self._db:
            try:
                cursor = self._db.execute("""
                    SELECT key, created_at, ttl_seconds FROM memory_entries
                    WHERE ttl_seconds IS NOT NULL
                """)
                now = time.time()
                for row in cursor:
                    created = datetime.fromisoformat(row['created_at']).timestamp()
                    if now - created > row['ttl_seconds']:
                        self.delete(row['key'])
                        removed += 1
            except Exception as e:
                self.logger.error(f"Cleanup failed: {e}")

        return removed

    def close(self) -> None:
        """Close database connection."""
        if self._db:
            self._db.close()
            self._db = None
