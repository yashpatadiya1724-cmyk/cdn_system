"""
Unit tests for Redis-style in-memory LRU cache engine.
"""

import pytest
from backend.redis_lru_cache import RedisLRUCache


def test_cache_miss():
    cache = RedisLRUCache(max_items=3, default_ttl_sec=10)
    res = cache.get("/images/banner.jpg")
    assert res["hit"] is False
    assert res["data"] is None


def test_cache_set_and_hit():
    cache = RedisLRUCache(max_items=3, default_ttl_sec=10)
    etag = cache.set("/images/banner.jpg", b"fake_binary_jpeg_bytes_123", content_type="image/jpeg")
    assert etag is not None

    res = cache.get("/images/banner.jpg")
    assert res["hit"] is True
    assert res["content_type"] == "image/jpeg"
    assert res["etag"] == etag
    assert res["not_modified"] is False
    assert res["data"] == b"fake_binary_jpeg_bytes_123"


def test_http_304_etag_validation():
    cache = RedisLRUCache(max_items=3, default_ttl_sec=10)
    etag = cache.set("/images/banner.jpg", b"fake_binary_jpeg_bytes_123", content_type="image/jpeg")

    # Matching client ETag must return HTTP 304 Not Modified
    res = cache.get("/images/banner.jpg", client_etag=etag)
    assert res["hit"] is True
    assert res["not_modified"] is True
    assert res["data"] is None


def test_lru_eviction_under_capacity():
    cache = RedisLRUCache(max_items=3, default_ttl_sec=10)
    cache.set("/item1", b"data1")
    cache.set("/item2", b"data2")
    cache.set("/item3", b"data3")

    # Touch /item1 so /item2 becomes the least recently used
    res1 = cache.get("/item1")
    assert res1["hit"] is True

    # Inserting 4th item triggers eviction of /item2
    cache.set("/item4", b"data4")

    assert cache.get("/item2")["hit"] is False
    assert cache.get("/item1")["hit"] is True
    assert cache.get("/item3")["hit"] is True
    assert cache.get("/item4")["hit"] is True


def test_telemetry_stats():
    cache = RedisLRUCache(max_items=3, default_ttl_sec=10)
    cache.set("/a", b"1")
    cache.set("/b", b"2")
    cache.get("/a")  # hit
    cache.get("/c")  # miss

    telemetry = cache.get_telemetry()
    assert telemetry["total_items"] == 2
    assert telemetry["hits"] >= 1
    assert telemetry["misses"] >= 1
    assert "hit_ratio_percent" in telemetry
