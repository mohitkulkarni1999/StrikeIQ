"""
Redis-based caching service for StrikeIQ backend.
Provides high-performance caching for expensive API calls and computations.
"""

import json
import logging
from typing import Any, Optional, Dict
import redis.asyncio as redis
from datetime import timedelta

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service with TTL support"""
    
    def __init__(self):
        self.redis_client = None
    
    async def _get_client(self):
        """Get Redis client with lazy initialization"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(
                    "redis://localhost:6379/0",
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Cache service connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_client = None
        return self.redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            client = await self._get_client()
            if not client:
                return None
            
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (default 5 minutes)"""
        try:
            client = await self._get_client()
            if not client:
                return False
            
            serialized_value = json.dumps(value, default=str)
            await client.setex(key, ttl, serialized_value)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            client = await self._get_client()
            if not client:
                return False
            
            await client.delete(key)
            logger.debug(f"Cache deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        try:
            client = await self._get_client()
            if not client:
                return 0
            
            keys = await client.keys(pattern)
            if keys:
                deleted_count = await client.delete(*keys)
                logger.info(f"Cache cleared {deleted_count} keys for pattern: {pattern}")
                return deleted_count
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

# Global cache instance
cache_service = CacheService()
