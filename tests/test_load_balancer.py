"""
Unit tests for CDN Load Balancer routing logic and failover.
"""

import pytest
from fastapi import HTTPException
from backend.load_balancer import pick_server, server_pool


def test_pick_server_balances_least_requests():
    # Save original pool state
    original_state = [{**s} for s in server_pool]

    try:
        # Mock pool with 2 healthy servers
        for s in server_pool:
            s["healthy"] = True
            s["requests"] = 0

        server_pool[0]["requests"] = 5
        server_pool[1]["requests"] = 2

        # pick_server should choose server 1 because it has fewer requests
        chosen = pick_server()
        assert chosen["id"] == server_pool[1]["id"]
        assert chosen["requests"] == 2
    finally:
        # Restore original state
        for idx, s in enumerate(original_state):
            server_pool[idx] = s


def test_pick_server_skips_unhealthy_servers():
    original_state = [{**s} for s in server_pool]

    try:
        # Mark server 0 as unhealthy even though it has 0 requests
        server_pool[0]["healthy"] = False
        server_pool[0]["requests"] = 0

        server_pool[1]["healthy"] = True
        server_pool[1]["requests"] = 10

        chosen = pick_server()
        assert chosen["id"] == server_pool[1]["id"]
    finally:
        for idx, s in enumerate(original_state):
            server_pool[idx] = s


def test_pick_server_raises_503_when_no_healthy_edges():
    original_state = [{**s} for s in server_pool]

    try:
        for s in server_pool:
            s["healthy"] = False

        with pytest.raises(HTTPException) as exc_info:
            pick_server()

        assert exc_info.value.status_code == 503
        assert "No healthy edge servers" in exc_info.value.detail
    finally:
        for idx, s in enumerate(original_state):
            server_pool[idx] = s


import asyncio
from unittest import mock
from fastapi.testclient import TestClient
from backend.load_balancer import app


def test_load_balancer_lifespan_starts_and_cancels_background_task():
    task_ref = None
    orig_create_task = asyncio.create_task

    def mock_create_task(coro):
        nonlocal task_ref
        task = orig_create_task(coro)
        task_ref = task
        return task

    with mock.patch("backend.load_balancer.asyncio.create_task", side_effect=mock_create_task):
        with TestClient(app) as client:
            assert task_ref is not None
            assert not task_ref.done()

        assert task_ref.done()
        assert task_ref.cancelled()


def test_load_balancer_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "up"
        assert data["server"] == "load_balancer"
        assert "healthy_edges" in data


def test_load_balancer_stats_endpoint():
    with TestClient(app) as client:
        # Mock httpx.AsyncClient.get for edge stats aggregation
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {
            "edge_id": "edge_1",
            "uptime_seconds": 120,
            "requests": 15,
            "cache_hits": 10,
            "cache_misses": 5,
        }

        async def mock_async_get(*args, **kwargs):
            return mock_response

        with mock.patch("httpx.AsyncClient.get", side_effect=mock_async_get):
            response = client.get("/stats")
            assert response.status_code == 200
            data = response.json()
            assert "load_balancer" in data
            assert data["load_balancer"]["total_requests"] >= 0
            assert "servers" in data
            assert len(data["servers"]) > 0
            assert "edge_details" in data
            assert len(data["edge_details"]) == len(data["servers"])


def test_load_balancer_clear_all_caches():
    with TestClient(app) as client:
        mock_response = mock.MagicMock()
        mock_response.status_code = 200

        async def mock_async_delete(*args, **kwargs):
            return mock_response

        with mock.patch("httpx.AsyncClient.delete", side_effect=mock_async_delete):
            response = client.delete("/cache")
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            for result in data["results"]:
                assert result["status"] == "cleared"


def test_load_balancer_proxy_success():
    with TestClient(app) as client:
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"Mock CDN File Content"
        mock_response.headers = {
            "content-type": "text/plain",
            "X-Cache": "HIT",
        }

        async def mock_async_get(*args, **kwargs):
            return mock_response

        with mock.patch("httpx.AsyncClient.get", side_effect=mock_async_get):
            response = client.get("/cdn/assets/mock_logo.png")
            assert response.status_code == 200
            assert response.content == b"Mock CDN File Content"
            assert "X-Routed-To" in response.headers
            assert response.headers["X-Cache"] == "HIT"

