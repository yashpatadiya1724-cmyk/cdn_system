"""
Unit Tests for PyCDN Distributed Global Edge Cache Eviction Engine
"""

import pytest
import shutil
import tempfile
from pathlib import Path
from backend.cache_manager import CacheManager
from backend.edge_eviction import EdgeEvictionEngine


@pytest.fixture
def test_env():
    temp_dir = tempfile.mkdtemp()
    cache_dir = Path(temp_dir) / "test_cache"
    cm = CacheManager(cache_dir=cache_dir, ttl=300, max_size_mb=10)
    engine = EdgeEvictionEngine(cache_manager=cm, node_id="edge-mumbai-01")
    yield cm, engine
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_purge_by_tag(test_env):
    """Verify surrogate key tag invalidation only evicts tagged assets."""
    cm, engine = test_env

    # Populate cache
    await cm.put("/catalog/shoes/sneaker.png", b"IMAGE_DATA_1", "image/png")
    await cm.put("/catalog/shoes/boots.png", b"IMAGE_DATA_2", "image/png")
    await cm.put("/catalog/shirts/tshirt.png", b"IMAGE_DATA_3", "image/png")

    # Register tags
    engine.register_tags("/catalog/shoes/sneaker.png", ["tag:footwear", "tag:promo"])
    engine.register_tags("/catalog/shoes/boots.png", ["tag:footwear"])
    engine.register_tags("/catalog/shirts/tshirt.png", ["tag:apparel"])

    # Invalidate tag:footwear
    res = await engine.purge_by_tag("tag:footwear")
    assert res["status"] == "success"
    assert res["evicted_count"] == 2
    assert res["reclaimed_bytes"] == len(b"IMAGE_DATA_1") + len(b"IMAGE_DATA_2")

    # Footwear items must be gone from cache
    assert await cm.get("/catalog/shoes/sneaker.png") is None
    assert await cm.get("/catalog/shoes/boots.png") is None

    # Apparel item must still be cached
    cached_shirt = await cm.get("/catalog/shirts/tshirt.png")
    assert cached_shirt is not None
    assert cached_shirt[0] == b"IMAGE_DATA_3"


@pytest.mark.asyncio
async def test_purge_by_pattern(test_env):
    """Verify glob/wildcard path pattern invalidation."""
    cm, engine = test_env

    await cm.put("/static/v1/app.js", b"console.log('v1')", "application/javascript")
    await cm.put("/static/v1/style.css", b"body { color: red; }", "text/css")
    await cm.put("/static/v2/app.js", b"console.log('v2')", "application/javascript")
    await cm.put("/api/users", b'{"users": []}', "application/json")

    # Invalidate /static/v1/*
    res = await engine.purge_by_pattern("/static/v1/*")
    assert res["status"] == "success"
    assert res["evicted_count"] == 2

    assert await cm.get("/static/v1/app.js") is None
    assert await cm.get("/static/v1/style.css") is None

    # v2 and api should still be cached
    assert await cm.get("/static/v2/app.js") is not None
    assert await cm.get("/api/users") is not None


@pytest.mark.asyncio
async def test_cluster_broadcast_application(test_env):
    """Verify remote eviction broadcast message handling."""
    cm, engine = test_env

    await cm.put("/media/hls/playlist.m3u8", b"#EXTM3U", "application/vnd.apple.mpegurl")
    engine.register_tags("/media/hls/playlist.m3u8", ["tag:live-stream"])

    # Simulate receiving broadcast payload from Frankfurt node
    broadcast_msg = {
        "version": "1.0",
        "action": "purge_tag",
        "target": "tag:live-stream",
        "origin_node": "edge-frankfurt-02"
    }

    result = await engine.apply_remote_eviction(broadcast_msg)
    assert result["status"] == "success"
    assert result["evicted_count"] == 1
    assert await cm.get("/media/hls/playlist.m3u8") is None
