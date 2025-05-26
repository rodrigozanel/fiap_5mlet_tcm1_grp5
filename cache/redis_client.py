"""
Redis client configuration and connection management.
"""

import os
import redis
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get or create Redis client instance.
    
    Returns:
        redis.Redis: Redis client instance or None if connection fails
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            # Get Redis configuration from environment variables
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            redis_password = os.getenv('REDIS_PASSWORD', None)
            
            # Create Redis client
            _redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            _redis_client.ping()
            logger.info(f"Redis client connected to {redis_host}:{redis_port}")
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            _redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            _redis_client = None
    
    return _redis_client


def is_redis_available() -> bool:
    """
    Check if Redis is available and responsive.
    
    Returns:
        bool: True if Redis is available, False otherwise
    """
    try:
        client = get_redis_client()
        if client is None:
            return False
        client.ping()
        return True
    except Exception as e:
        logger.warning(f"Redis availability check failed: {e}")
        return False


def reset_redis_client():
    """
    Reset the Redis client instance (useful for testing or reconnection).
    """
    global _redis_client
    if _redis_client:
        try:
            _redis_client.close()
        except Exception as e:
            logger.warning(f"Error closing Redis client: {e}")
    _redis_client = None 