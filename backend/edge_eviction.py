"""
edge_eviction.py
Distributed Global Edge Cache Eviction Engine for PyCDN.
Supports Tag-based (Surrogate-Keys), Prefix/Wildcard pattern invalidation,
and Multi-Node Cluster Eviction Event Broadcasts.
"""

import time
import fnmatch
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.cache_manager import CacheManager

logger = logging.getLogger("cdn.eviction")


class EdgeEvictionEngine:
    """
    Coordinates granular and cluster-wide cache invalidation across distributed edge nodes.
    Supports tag invalidation (surrogate keys), regex/glob path patterns, and audit telemetry.
    """

    def __init__(self, cache_manager: CacheManager, node_id: str = "edge-node-primary"):
        self.cache_manager = cache_manager
        self.node_id = node_id
        # Tag to set of cache keys index: tag -> set(keys)
        self._tag_index: Dict[str, set] = {}
        # Key to set of tags index: key -> set(tags)
        self._key_tags: Dict[str, set] = {}
        self._eviction_history: List[Dict[str, Any]] = []

    def register_tags(self, file_path: str, tags: List[str]):
        """Associates cache tags (surrogate keys) with a cached resource path."""
        key = self.cache_manager._key(file_path)
        if key not in self._key_tags:
            self._key_tags[key] = set()

        for tag in tags:
            clean_tag = tag.strip().lower()
            self._key_tags[key].add(clean_tag)
            if clean_tag not in self._tag_index:
                self._tag_index[clean_tag] = set()
            self._tag_index[clean_tag].add(key)

    async def purge_by_tag(self, tag: str) -> Dict[str, Any]:
        """
        Invalidates all cached entries tagged with the given surrogate key.
        """
        start_time = time.time()
        clean_tag = tag.strip().lower()
        matched_keys = list(self._tag_index.get(clean_tag, set()))

        reclaimed_bytes = 0
        evicted_paths = []

        async with self.cache_manager._lock:
            for key in matched_keys:
                meta = self.cache_manager._meta.get(key)
                if meta:
                    reclaimed_bytes += meta.get("size", 0)
                    evicted_paths.append(meta.get("path", key))
                await self.cache_manager._evict(key)

                # Clean up reverse index
                if key in self._key_tags:
                    for t in self._key_tags[key]:
                        if t in self._tag_index:
                            self._tag_index[t].discard(key)
                    del self._key_tags[key]

        duration_ms = round((time.time() - start_time) * 1000, 2)
        telemetry = {
            "status": "success",
            "type": "TAG_PURGE",
            "tag": clean_tag,
            "evicted_count": len(evicted_paths),
            "reclaimed_bytes": reclaimed_bytes,
            "duration_ms": duration_ms,
            "evicted_paths": evicted_paths,
            "timestamp": time.time(),
            "node_id": self.node_id,
        }
        self._record_telemetry(telemetry)
        logger.info(f"TAG PURGE [{clean_tag}]: {len(evicted_paths)} keys evicted, {reclaimed_bytes} bytes freed")
        return telemetry

    async def purge_by_pattern(self, pattern: str) -> Dict[str, Any]:
        """
        Invalidates cached entries matching a glob path pattern (e.g., '/images/*', '*/v2/*').
        """
        start_time = time.time()
        evicted_paths = []
        reclaimed_bytes = 0

        async with self.cache_manager._lock:
            # Match paths in meta against glob pattern
            keys_to_evict = []
            for key, meta in list(self.cache_manager._meta.items()):
                path = meta.get("path", "")
                if fnmatch.fnmatch(path, pattern):
                    keys_to_evict.append((key, path, meta.get("size", 0)))

            for key, path, size in keys_to_evict:
                reclaimed_bytes += size
                evicted_paths.append(path)
                await self.cache_manager._evict(key)
                # Cleanup tag indices
                if key in self._key_tags:
                    for t in self._key_tags[key]:
                        if t in self._tag_index:
                            self._tag_index[t].discard(key)
                    del self._key_tags[key]

        duration_ms = round((time.time() - start_time) * 1000, 2)
        telemetry = {
            "status": "success",
            "type": "PATTERN_PURGE",
            "pattern": pattern,
            "evicted_count": len(evicted_paths),
            "reclaimed_bytes": reclaimed_bytes,
            "duration_ms": duration_ms,
            "evicted_paths": evicted_paths,
            "timestamp": time.time(),
            "node_id": self.node_id,
        }
        self._record_telemetry(telemetry)
        logger.info(f"PATTERN PURGE [{pattern}]: {len(evicted_paths)} keys evicted, {reclaimed_bytes} bytes freed")
        return telemetry

    def create_eviction_broadcast_payload(self, action: str, target: str) -> Dict[str, Any]:
        """
        Generates a standardized cluster broadcast message for edge gossip / Redis pub/sub.
        action: 'purge_tag' | 'purge_pattern' | 'purge_all'
        """
        return {
            "version": "1.0",
            "action": action,
            "target": target,
            "origin_node": self.node_id,
            "broadcast_time": time.time(),
        }

    async def apply_remote_eviction(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies an eviction broadcast dispatched from a peer edge node.
        """
        action = message.get("action")
        target = message.get("target")

        if action == "purge_tag":
            return await self.purge_by_tag(target)
        elif action == "purge_pattern":
            return await self.purge_by_pattern(target)
        elif action == "purge_all":
            await self.cache_manager.clear_all()
            self._tag_index.clear()
            self._key_tags.clear()
            return {
                "status": "success",
                "type": "PURGE_ALL",
                "origin_node": message.get("origin_node"),
                "applied_by": self.node_id,
            }
        else:
            return {"status": "error", "message": f"Unknown eviction action: {action}"}

    def _record_telemetry(self, item: Dict[str, Any]):
        self._eviction_history.append(item)
        if len(self._eviction_history) > 100:
            self._eviction_history.pop(0)

    def get_eviction_history(self) -> List[Dict[str, Any]]:
        return list(self._eviction_history)
