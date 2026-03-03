"""
Production Redis Client with Connection Pooling
Optimized for high-performance async operations
"""

import redis.asyncio as redis
import logging
from typing import Optional, Any, Union, List
import json
from contextlib import asynccontextmanager
from ..core.config import settings

logger = logging.getLogger(__name__)

class ProductionRedisClient:
    """Production-grade Redis client with connection pooling"""
    
    def __init__(self):
        self.pool: Optional[redis.ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connection pool"""
        if self._initialized:
            return
        
        try:
            # Create connection pool
            self.pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                decode_responses=True
            )
            
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.client.ping()
            self._initialized = True
            logger.info("✅ Production Redis pool initialized")
            
        except Exception as e:
            logger.error(f"❌ Redis pool initialization failed: {e}")
            raise
    
    async def close(self):
        """Close Redis connection pool"""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
        self._initialized = False
        logger.info("✅ Redis pool closed")
    
    @asynccontextmanager
    async def get_client(self):
        """Get Redis client from pool"""
        if not self._initialized:
            await self.initialize()
        yield self.client
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        async with self.get_client() as client:
            try:
                return await client.get(key)
            except Exception as e:
                logger.error(f"Redis GET failed for {key}: {e}")
                return None
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration"""
        async with self.get_client() as client:
            try:
                return await client.set(key, value, ex=ex)
            except Exception as e:
                logger.error(f"Redis SET failed for {key}: {e}")
                return False
    
    async def set_json(self, key: str, data: dict, ex: Optional[int] = None) -> bool:
        """Set JSON data in Redis"""
        try:
            json_str = json.dumps(data)
            return await self.set(key, json_str, ex)
        except Exception as e:
            logger.error(f"Redis SET JSON failed for {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON data from Redis"""
        try:
            value = await self.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET JSON failed for {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        async with self.get_client() as client:
            try:
                return await client.delete(key) > 0
            except Exception as e:
                logger.error(f"Redis DELETE failed for {key}: {e}")
                return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        async with self.get_client() as client:
            try:
                return await client.exists(key) > 0
            except Exception as e:
                logger.error(f"Redis EXISTS failed for {key}: {e}")
                return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        async with self.get_client() as client:
            try:
                return await client.expire(key, seconds)
            except Exception as e:
                logger.error(f"Redis EXPIRE failed for {key}: {e}")
                return False
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        async with self.get_client() as client:
            try:
                return await client.keys(pattern)
            except Exception as e:
                logger.error(f"Redis KEYS failed for pattern {pattern}: {e}")
                return []
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field"""
        async with self.get_client() as client:
            try:
                return await client.hget(key, field)
            except Exception as e:
                logger.error(f"Redis HGET failed for {key}.{field}: {e}")
                return None
    
    async def hset(self, key: str, field: str, value: str) -> bool:
        """Set hash field"""
        async with self.get_client() as client:
            try:
                return await client.hset(key, field, value) > 0
            except Exception as e:
                logger.error(f"Redis HSET failed for {key}.{field}: {e}")
                return False
    
    async def hgetall(self, key: str) -> dict:
        """Get all hash fields"""
        async with self.get_client() as client:
            try:
                return await client.hgetall(key)
            except Exception as e:
                logger.error(f"Redis HGETALL failed for {key}: {e}")
                return {}
    
    async def lpush(self, key: str, *values) -> int:
        """Push values to list head"""
        async with self.get_client() as client:
            try:
                return await client.lpush(key, *values)
            except Exception as e:
                logger.error(f"Redis LPUSH failed for {key}: {e}")
                return 0
    
    async def rpop(self, key: str) -> Optional[str]:
        """Pop value from list tail"""
        async with self.get_client() as client:
            try:
                return await client.rpop(key)
            except Exception as e:
                logger.error(f"Redis RPOP failed for {key}: {e}")
                return None
    
    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get range of list values"""
        async with self.get_client() as client:
            try:
                return await client.lrange(key, start, end)
            except Exception as e:
                logger.error(f"Redis LRANGE failed for {key}: {e}")
                return []
    
    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel"""
        async with self.get_client() as client:
            try:
                return await client.publish(channel, message)
            except Exception as e:
                logger.error(f"Redis PUBLISH failed for {channel}: {e}")
                return 0
    
    async def subscribe(self, *channels) -> Any:
        """Subscribe to channels"""
        async with self.get_client() as client:
            try:
                return await client.subscribe(*channels)
            except Exception as e:
                logger.error(f"Redis SUBSCRIBE failed: {e}")
                return None
    
    async def pipeline(self):
        """Get Redis pipeline for batch operations"""
        async with self.get_client() as client:
            return client.pipeline()
    
    async def test_connection(self) -> bool:
        """Test Redis connection"""
        try:
            async with self.get_client() as client:
                await client.ping()
                return True
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            return False

# Global Redis client instance
production_redis = ProductionRedisClient()

# Convenience functions for backward compatibility
async def get_redis_client() -> ProductionRedisClient:
    """Get Redis client instance"""
    return production_redis

# Legacy compatibility - direct access to client
redis_client = production_redis

async def test_redis_connection():
    """Test Redis connection during startup"""
    return await production_redis.test_connection()
