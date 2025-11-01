"""Redis connection management for caching and session state"""

import logging
import json
from typing import Optional, Any
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError

from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Global Redis client and connection pool
_redis_client: Optional[Redis] = None
_redis_pool: Optional[ConnectionPool] = None


async def connect_to_redis() -> Redis:
    """
    Initialize Redis connection with connection pooling.
    
    Returns:
        Redis: Redis client instance
        
    Raises:
        ConnectionError: If connection fails
    """
    global _redis_client, _redis_pool
    
    try:
        logger.info(f"Connecting to Redis: {settings.redis_url}")
        
        # Create connection pool
        _redis_pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30,
        )
        
        # Create Redis client
        _redis_client = Redis(connection_pool=_redis_pool)
        
        # Verify connection
        await _redis_client.ping()
        
        logger.info("✅ Connected to Redis")
        return _redis_client
        
    except (RedisError, ConnectionError) as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error connecting to Redis: {e}")
        raise


async def close_redis_connection():
    """Close Redis connection and cleanup resources."""
    global _redis_client, _redis_pool
    
    if _redis_client:
        logger.info("Closing Redis connection...")
        await _redis_client.close()
        _redis_client = None
    
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
        
    logger.info("✅ Redis connection closed")


def get_redis() -> Redis:
    """
    Get the Redis client instance.
    
    Returns:
        Redis: Redis client
        
    Raises:
        RuntimeError: If Redis is not initialized
    """
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call connect_to_redis() first.")
    return _redis_client


# Cache helper functions
class RedisCache:
    """Redis cache operations helper"""
    
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            redis = get_redis()
            value = await redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    @staticmethod
    async def set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            redis = get_redis()
            serialized = json.dumps(value)
            if ttl:
                await redis.setex(key, ttl, serialized)
            else:
                await redis.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    @staticmethod
    async def delete(key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            redis = get_redis()
            await redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    @staticmethod
    async def exists(key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            redis = get_redis()
            return bool(await redis.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    @staticmethod
    async def get_many(keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs
        """
        try:
            redis = get_redis()
            values = await redis.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
            return result
        except Exception as e:
            logger.error(f"Redis mget error: {e}")
            return {}
    
    @staticmethod
    async def set_many(items: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in cache.
        
        Args:
            items: Dictionary of key-value pairs
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            redis = get_redis()
            pipe = redis.pipeline()
            for key, value in items.items():
                serialized = json.dumps(value)
                if ttl:
                    pipe.setex(key, ttl, serialized)
                else:
                    pipe.set(key, serialized)
            await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Redis mset error: {e}")
            return False
    
    @staticmethod
    async def increment(key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter.
        
        Args:
            key: Counter key
            amount: Amount to increment
            
        Returns:
            New value or None on error
        """
        try:
            redis = get_redis()
            return await redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            return None
    
    @staticmethod
    async def expire(key: str, ttl: int) -> bool:
        """
        Set expiration on key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            redis = get_redis()
            return await redis.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False


# Job status cache helpers
class JobStatusCache:
    """Helper for caching job status"""
    
    @staticmethod
    def _get_key(job_id: str) -> str:
        """Get Redis key for job status"""
        return f"job:status:{job_id}"
    
    @staticmethod
    async def get_status(job_id: str) -> Optional[dict]:
        """Get job status from cache"""
        return await RedisCache.get(JobStatusCache._get_key(job_id))
    
    @staticmethod
    async def set_status(job_id: str, status: dict) -> bool:
        """Set job status in cache"""
        return await RedisCache.set(
            JobStatusCache._get_key(job_id),
            status,
            ttl=settings.cache_ttl_job_status
        )
    
    @staticmethod
    async def delete_status(job_id: str) -> bool:
        """Delete job status from cache"""
        return await RedisCache.delete(JobStatusCache._get_key(job_id))


# Translation cache helpers
class TranslationCache:
    """Helper for caching translations"""
    
    @staticmethod
    def _get_key(text_hash: str, source_lang: str, target_lang: str) -> str:
        """Get Redis key for translation"""
        return f"translation:{source_lang}:{target_lang}:{text_hash}"
    
    @staticmethod
    async def get_translation(text_hash: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Get cached translation"""
        return await RedisCache.get(
            TranslationCache._get_key(text_hash, source_lang, target_lang)
        )
    
    @staticmethod
    async def set_translation(
        text_hash: str,
        source_lang: str,
        target_lang: str,
        translation: str
    ) -> bool:
        """Set translation in cache"""
        return await RedisCache.set(
            TranslationCache._get_key(text_hash, source_lang, target_lang),
            translation,
            ttl=settings.cache_ttl_translation
        )


# TTS cache helpers
class TTSCache:
    """Helper for caching TTS audio metadata"""
    
    @staticmethod
    def _get_key(text_hash: str, voice: str, style: str) -> str:
        """Get Redis key for TTS"""
        return f"tts:{voice}:{style}:{text_hash}"
    
    @staticmethod
    async def get_audio_metadata(text_hash: str, voice: str, style: str) -> Optional[dict]:
        """Get cached TTS audio metadata"""
        return await RedisCache.get(TTSCache._get_key(text_hash, voice, style))
    
    @staticmethod
    async def set_audio_metadata(
        text_hash: str,
        voice: str,
        style: str,
        metadata: dict
    ) -> bool:
        """Set TTS audio metadata in cache"""
        return await RedisCache.set(
            TTSCache._get_key(text_hash, voice, style),
            metadata,
            ttl=settings.cache_ttl_tts
        )
