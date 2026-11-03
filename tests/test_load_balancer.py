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
