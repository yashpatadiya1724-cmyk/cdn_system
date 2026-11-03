"""
Unit tests for disk-backed CacheManager with TTL and statistics.
"""

import asyncio
import time
import shutil
from pathlib import Path
import pytest
from backend.cache_manager import CacheManager


@pytest.fixture
def temp_cache_dir(tmp_path):
    cache_dir = tmp_path / "test_edge_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    yield cache_dir
    if cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)


def test_cache_manager_put_and_get(temp_cache_dir):
    async def run():
        mgr = CacheManager(cache_dir=temp_cache_dir, ttl=10, max_size_mb=10)
        
        # Initial lookup is None
        miss = await mgr.get("/css/styles.css")
        assert miss is None

        # Store content
        test_data = b"body { background: #0f172a; color: #fff; }"
        await mgr.put("/css/styles.css", test_data, content_type="text/css")

        # Fetch cached content
        hit = await mgr.get("/css/styles.css")
        assert hit is not None
        data, content_type = hit
        assert data == test_data
        assert content_type == "text/css"

    asyncio.run(run())


def test_cache_manager_ttl_expiry(temp_cache_dir):
    async def run():
        # Short TTL of 1 second
        mgr = CacheManager(cache_dir=temp_cache_dir, ttl=1, max_size_mb=10)
        await mgr.put("/quick_expire.txt", b"temporary", content_type="text/plain")

        hit = await mgr.get("/quick_expire.txt")
        assert hit is not None

        # Manually backdate the entry expiration in metadata
        key = mgr._key("/quick_expire.txt")
        mgr._meta[key]["expires"] = time.time() - 5
        mgr._save_meta()

        # Next lookup should evict and return None
        expired = await mgr.get("/quick_expire.txt")
        assert expired is None

    asyncio.run(run())


def test_cache_manager_delete_and_clear(temp_cache_dir):
    async def run():
        mgr = CacheManager(cache_dir=temp_cache_dir, ttl=30, max_size_mb=10)
        await mgr.put("/file1.js", b"console.log('1')", content_type="application/javascript")
        await mgr.put("/file2.js", b"console.log('2')", content_type="application/javascript")

        # Delete single file
        deleted = await mgr.delete("/file1.js")
        assert deleted is True
        assert await mgr.get("/file1.js") is None
        assert await mgr.get("/file2.js") is not None

        # Clear all
        await mgr.clear_all()
        assert await mgr.get("/file2.js") is None
        assert mgr.stats()["total_entries"] == 0

    asyncio.run(run())


def test_cache_manager_stats(temp_cache_dir):
    async def run():
        mgr = CacheManager(cache_dir=temp_cache_dir, ttl=60, max_size_mb=5)
        payload = b"X" * 1024  # 1 KB
        await mgr.put("/blob.bin", payload, content_type="application/octet-stream")
        
        # Access twice to record hits
        await mgr.get("/blob.bin")
        await mgr.get("/blob.bin")

        stats = mgr.stats()
        assert stats["total_entries"] == 1
        assert stats["active_entries"] == 1
        assert stats["total_hits"] == 2

    asyncio.run(run())
