"""
Unit tests for Edge Server endpoints and caching behavior using FastAPI TestClient.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.edge_server import app, cache, stats


@pytest.fixture
def client():
    return TestClient(app)


def test_edge_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "up"
    assert data["server"] == "edge"
    assert "edge" in data["id"]
    assert "port" in data


def test_edge_stats_endpoint(client):
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "edge_id" in data
    assert "uptime_seconds" in data
    assert "requests" in data
    assert "cache_hits" in data
    assert "cache_misses" in data
    assert "hit_rate_pct" in data
    assert "cache" in data


def test_edge_clear_cache_endpoint(client):
    response = client.delete("/cache")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cleared"
    assert "edge" in data


def test_edge_evict_file_endpoint(client):
    response = client.delete("/cache/test_file.txt")
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == "test_file.txt"
    assert "evicted" in data


def test_edge_serve_cache_hit(client):
    test_path = "cached_banner.svg"
    test_content = b"<svg xmlns='http://www.w3.org/2000/svg'><text>PyCDN Edge</text></svg>"
    
    # Pre-populate cache directly
    asyncio.run(cache.put(test_path, test_content, "image/svg+xml"))
    
    response = client.get(f"/cdn/{test_path}")
    assert response.status_code == 200
    assert response.content == test_content
    assert response.headers.get("X-Cache") == "HIT"
    assert "image/svg+xml" in response.headers.get("content-type", "")
    assert response.headers.get("X-Cache-TTL") is not None


def test_edge_serve_origin_unreachable_503(client):
    # Requesting an uncached file with origin unreachable should return 503 or 502
    response = client.get("/cdn/non_existent_unreachable_asset.png")
    assert response.status_code in [502, 503]
    data = response.json()
    assert "detail" in data
