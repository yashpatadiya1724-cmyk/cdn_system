"""
Test Suite: PyCDN Redis In-Memory LRU Cache Engine
"""

from backend.redis_lru_cache import RedisLRUCache

def test_lru_cache_operations():
    print("Running PyCDN Redis LRU Cache Unit Tests...")
    cache = RedisLRUCache(max_items=3, default_ttl_sec=10)

    # Test 1: Cache Miss
    res1 = cache.get("/images/banner.jpg")
    assert res1["hit"] == False, "Initial lookup must be a cache miss"
    print("[PASS] Cache miss behavior verified")

    # Test 2: Cache Set & Hit
    etag1 = cache.set("/images/banner.jpg", b"fake_binary_jpeg_bytes_123", content_type="image/jpeg")
    res2 = cache.get("/images/banner.jpg")
    assert res2["hit"] == True, "Subsequent lookup must be a cache hit"
    assert res2["content_type"] == "image/jpeg"
    assert res2["etag"] == etag1
    assert res2["not_modified"] == False
    print(f"[PASS] Cache set & hit verified (ETag: {etag1})")

    # Test 3: HTTP 304 Not Modified validation
    res_304 = cache.get("/images/banner.jpg", client_etag=etag1)
    assert res_304["hit"] == True
    assert res_304["not_modified"] == True, "Matching client ETag must trigger 304 Not Modified"
    print("[PASS] HTTP 304 ETag revalidation verified")

    # Test 4: LRU Eviction under capacity limit
    cache.set("/item1", b"data1")
    cache.set("/item2", b"data2")
    # Current keys in cache (max_items=3): /images/banner.jpg, /item1, /item2

    # Access /images/banner.jpg so it becomes most recently used
    cache.get("/images/banner.jpg")

    # Adding a 4th item must evict /item1 (least recently used)
    cache.set("/item3", b"data3")

    evicted_lookup = cache.get("/item1")
    assert evicted_lookup["hit"] == False, "/item1 must have been evicted by LRU algorithm"

    retained_lookup = cache.get("/images/banner.jpg")
    assert retained_lookup["hit"] == True, "/images/banner.jpg was recently accessed and must be retained"
    print("[PASS] O(1) Least-Recently-Used (LRU) eviction policy verified")

    # Test 5: Telemetry stats
    telemetry = cache.get_telemetry()
    assert telemetry["total_items"] == 3
    assert telemetry["evictions"] >= 1
    assert telemetry["hit_ratio_percent"] > 50.0
    print(f"[PASS] Edge telemetry verified: Hit Ratio = {telemetry['hit_ratio_percent']}%")

    print("ALL PyCDN REDIS LRU CACHE TESTS PASSED SUCCESSFULLY! [OK]")

if __name__ == "__main__":
    test_lru_cache_operations()
