"""
Tests for core.memory module.

Covers:
    - Basic CRUD operations (write, read, delete, exists)
    - Namespace isolation
    - Search functionality
    - SQLite metadata tracking
    - Cache behavior
    - TTL/expiry
    - Statistics
"""

import os
import json
import shutil
import tempfile
import pytest

from core.memory import Memory


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    d = tempfile.mkdtemp(prefix="arcyn_test_memory_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def memory(temp_dir):
    """Create a Memory instance with temp storage."""
    return Memory(storage_path=temp_dir, enable_db=True)


class TestMemoryWrite:
    """Tests for memory write operations."""

    def test_write_simple(self, memory):
        """Write a simple value and verify."""
        assert memory.write("test_key", {"value": 42}) is True

    def test_write_creates_file(self, memory, temp_dir):
        """Write should create a JSON file."""
        memory.write("mydata", {"hello": "world"})
        file_path = os.path.join(temp_dir, "mydata.json")
        assert os.path.exists(file_path)

        with open(file_path, 'r') as f:
            data = json.load(f)
        assert data == {"hello": "world"}

    def test_write_with_namespace(self, memory):
        """Write with namespace should succeed."""
        assert memory.write("plan_1", {"goal": "Build API"},
                           namespace="architect") is True

    def test_write_with_metadata(self, memory):
        """Write with metadata should track extra info."""
        assert memory.write("tagged_entry", {"data": 1},
                           tags=["important", "test"],
                           metadata={"source": "unit_test"}) is True

    def test_write_overwrite(self, memory):
        """Writing to same key should overwrite."""
        memory.write("key1", {"v": 1})
        memory.write("key1", {"v": 2})
        assert memory.read("key1") == {"v": 2}


class TestMemoryRead:
    """Tests for memory read operations."""

    def test_read_existing(self, memory):
        """Read existing key should return data."""
        memory.write("readtest", {"a": 1, "b": "hello"})
        result = memory.read("readtest")
        assert result == {"a": 1, "b": "hello"}

    def test_read_missing(self, memory):
        """Read missing key should return None."""
        assert memory.read("nonexistent") is None

    def test_read_from_cache(self, memory):
        """Second read should come from cache."""
        memory.write("cached", {"fast": True})
        # First read
        memory.read("cached")
        # Clear the file to prove cache is used
        os.remove(os.path.join(str(memory.storage_path), "cached.json"))
        # Should still return from cache
        assert memory.read("cached") == {"fast": True}

    def test_read_from_disk(self, memory):
        """Read should fall back to disk when cache is empty."""
        memory.write("disktest", {"disk": True})
        # Clear cache
        memory._cache.clear()
        # Should load from disk
        result = memory.read("disktest")
        assert result == {"disk": True}


class TestMemoryDelete:
    """Tests for memory delete operations."""

    def test_delete_existing(self, memory):
        """Delete should remove from cache, file, and DB."""
        memory.write("del_me", {"data": 1})
        assert memory.delete("del_me") is True
        assert memory.read("del_me") is None
        assert memory.exists("del_me") is False

    def test_delete_nonexistent(self, memory):
        """Delete nonexistent key should succeed gracefully."""
        assert memory.delete("ghost_key") is True


class TestMemoryExists:
    """Tests for memory exists operations."""

    def test_exists_true(self, memory):
        """Exists should return True for written key."""
        memory.write("existtest", {"here": True})
        assert memory.exists("existtest") is True

    def test_exists_false(self, memory):
        """Exists should return False for missing key."""
        assert memory.exists("nope") is False


class TestMemorySearch:
    """Tests for memory search operations."""

    def test_search_by_pattern(self, memory):
        """Search should find entries matching pattern."""
        memory.write("plan_alpha", {"id": 1}, namespace="plans")
        memory.write("plan_beta", {"id": 2}, namespace="plans")
        memory.write("build_alpha", {"id": 3}, namespace="builds")

        results = memory.search("plan")
        keys = [r['key'] for r in results]
        assert "plan_alpha" in keys
        assert "plan_beta" in keys
        assert "build_alpha" not in keys

    def test_search_by_namespace(self, memory):
        """Search with namespace should filter results."""
        memory.write("a_1", {"v": 1}, namespace="ns_a")
        memory.write("a_2", {"v": 2}, namespace="ns_b")

        results = memory.search("a_", namespace="ns_a")
        assert len(results) == 1
        assert results[0]['key'] == "a_1"

    def test_search_empty(self, memory):
        """Search with no matches should return empty list."""
        results = memory.search("zzzzz_no_match")
        assert results == []


class TestMemoryStats:
    """Tests for memory statistics."""

    def test_stats_basic(self, memory):
        """Stats should return valid dictionary."""
        stats = memory.get_stats()
        assert isinstance(stats, dict)
        assert 'cache_entries' in stats
        assert 'db_enabled' in stats

    def test_stats_after_writes(self, memory):
        """Stats should reflect written entries."""
        memory.write("s1", {"v": 1}, namespace="test")
        memory.write("s2", {"v": 2}, namespace="test")
        stats = memory.get_stats()
        assert stats['cache_entries'] == 2

    def test_list_keys(self, memory):
        """List keys should return all keys."""
        memory.write("k1", {"v": 1})
        memory.write("k2", {"v": 2})
        keys = memory.list_keys()
        assert "k1" in keys
        assert "k2" in keys


class TestMemoryDB:
    """Tests for SQLite database features."""

    def test_db_file_created(self, temp_dir):
        """SQLite database file should be created."""
        Memory(storage_path=temp_dir, enable_db=True)
        db_path = os.path.join(temp_dir, "memory_index.db")
        assert os.path.exists(db_path)

    def test_db_disabled(self, temp_dir):
        """Memory should work without database."""
        mem = Memory(storage_path=temp_dir, enable_db=False)
        mem.write("no_db", {"works": True})
        assert mem.read("no_db") == {"works": True}

    def test_access_tracking(self, memory):
        """Read should increment access count."""
        memory.write("tracked", {"v": 1})
        memory.read("tracked")
        memory.read("tracked")
        memory.read("tracked")
        # Access count should be 3
        if memory._db:
            cursor = memory._db.execute(
                "SELECT access_count FROM memory_entries WHERE key = ?",
                ("tracked",)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row['access_count'] == 3
