"""
PaperGraph V3 - Optional Redis Backend (Phase 10)
Provides seamless local memory/file caching when Redis is absent.
Zero mandatory external daemon dependencies.
"""
import os
import logging
from typing import Optional, Any, Dict

logger = logging.getLogger("papergraph.v3.redis")

class RedisBackendManager:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", None)
        self._client = None
        self._memory_cache: Dict[str, Any] = {}
        self.is_connected = False
        self._init_connection()

    def _init_connection(self):
        if not self.redis_url:
            logger.info("REDIS_URL not set; using local-first in-memory cache backend.")
            return

        try:
            import redis
            self._client = redis.from_url(self.redis_url, socket_timeout=1.0)
            self._client.ping()
            self.is_connected = True
            logger.info("Connected to Redis cache backend.")
        except ImportError:
            logger.info("redis package not installed; utilizing local memory backend.")
        except Exception as e:
            logger.info(f"Redis unavailable ({e}); gracefully falling back to local memory backend.")
            self._client = None
            self.is_connected = False

    def get(self, key: str, default: Any = None) -> Any:
        if self.is_connected and self._client:
            try:
                val = self._client.get(key)
                return val.decode("utf-8") if val else default
            except Exception:
                pass
        return self._memory_cache.get(key, default)

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        if self.is_connected and self._client:
            try:
                self._client.set(key, value, ex=ttl_seconds)
                return True
            except Exception:
                pass
        self._memory_cache[key] = value
        return True

    def delete(self, key: str) -> bool:
        if self.is_connected and self._client:
            try:
                self._client.delete(key)
            except Exception:
                pass
        self._memory_cache.pop(key, None)
        return True

redis_backend = RedisBackendManager()

