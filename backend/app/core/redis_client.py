import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

# Redis client for distributed locking and shared state
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

async def test_redis_connection():
    """Test Redis connection during startup"""
    try:
        await redis_client.ping()
        logger.info("✅ Redis connection established")
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False
