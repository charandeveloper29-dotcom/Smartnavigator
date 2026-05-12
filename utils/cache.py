"""
Simple In-Memory Cache Module
Provides TTL-based caching to reduce file I/O
"""

import time
import threading


class SimpleCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()

    def get(self, key):
        """Get a cached value. Returns None if expired or not found."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expiry = entry
            if time.time() > expiry:
                del self._store[key]
                return None
            return value

    def set(self, key, value, ttl=300):
        """Store a value with TTL in seconds (default: 5 minutes)."""
        with self._lock:
            self._store[key] = (value, time.time() + ttl)

    def delete(self, key):
        """Remove a cached entry."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._store.clear()

    def invalidate_prefix(self, prefix):
        """Remove all entries whose keys start with a given prefix."""
        with self._lock:
            keys_to_del = [k for k in self._store if k.startswith(prefix)]
            for key in keys_to_del:
                del self._store[key]

    def stats(self):
        """Return cache statistics."""
        with self._lock:
            now = time.time()
            active = sum(1 for _, (_, exp) in self._store.items() if exp > now)
            return {'total_keys': len(self._store), 'active_keys': active}


# Global cache instance
cache = SimpleCache()
