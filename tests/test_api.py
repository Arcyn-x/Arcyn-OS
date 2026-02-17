"""
Tests for the REST API server.

Covers:
    - App creation
    - Health check
    - Status endpoint
    - Execute endpoint
    - Classify endpoint
    - Memory endpoints
"""

import pytest

try:
    from fastapi.testclient import TestClient
    from api.server import create_app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


@pytest.fixture
def client():
    """Create a test client."""
    if not HAS_FASTAPI:
        pytest.skip("FastAPI not installed")
    app = create_app()
    return TestClient(app)


class TestAPIHealth:
    """Tests for health and root endpoints."""

    def test_root(self, client):
        """Root should return app info."""
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data['name'] == "Arcyn OS"

    def test_health(self, client):
        """Health check should return healthy."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()['status'] == "healthy"


class TestAPIStatus:
    """Tests for status endpoint."""

    def test_status(self, client):
        """Status should return agent info."""
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert 'agents' in data
        assert 'agents_total' in data


class TestAPIExecute:
    """Tests for execute endpoint."""

    def test_execute(self, client):
        """Execute should accept a goal and return result."""
        resp = client.post("/api/execute", json={"goal": "Test goal"})
        assert resp.status_code == 200
        data = resp.json()
        assert 'status' in data
        assert 'stages' in data

    def test_execute_empty_goal(self, client):
        """Execute with empty goal should return 422."""
        resp = client.post("/api/execute", json={"goal": ""})
        assert resp.status_code == 422


class TestAPIClassify:
    """Tests for classify endpoint."""

    def test_classify(self, client):
        """Classify should return intent classification."""
        resp = client.post("/api/classify", json={"input": "Build a REST API"})
        assert resp.status_code == 200
        data = resp.json()
        assert 'goal' in data or 'intent' in data


class TestAPIMemory:
    """Tests for memory endpoints."""

    def test_memory_search(self, client):
        """Memory search should return results array."""
        resp = client.get("/api/memory/search?pattern=test")
        assert resp.status_code == 200
        data = resp.json()
        assert 'results' in data

    def test_memory_stats(self, client):
        """Memory stats should return statistics."""
        resp = client.get("/api/memory/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert 'cache_entries' in data
