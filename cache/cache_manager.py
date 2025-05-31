"""
Cache manager for handling short-term and fallback caching strategies.
"""

import os
import json
import hashlib
import logging
from typing import Any, Optional, Dict, Union
from datetime import datetime, timezone

from .redis_client import get_redis_client, is_redis_available

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages two-layer caching system:
    1. Short-term cache: For HTTP request responses (default: 5 minutes)
    2. Fallback cache: For web scraping data when source is unavailable (default: 30 days)
    """
    
    def __init__(self):
        # Get cache TTL values from environment variables
        self.short_cache_ttl = int(os.getenv('SHORT_CACHE_TTL', 300))  # 5 minutes
        self.fallback_cache_ttl = int(os.getenv('FALLBACK_CACHE_TTL', 2592000))  # 30 days
        
        # Cache key prefixes
        self.short_cache_prefix = "short:"
        self.fallback_cache_prefix = "fallback:"
        
        # Initialize Redis client
        self.redis_client = get_redis_client()
    
    def _generate_cache_key(self, prefix: str, endpoint: str, params: Dict[str, Any] = None) -> str:
        """
        Generate a unique cache key based on endpoint and parameters.
        
        Args:
            prefix: Cache prefix (short: or fallback:)
            endpoint: API endpoint name
            params: Request parameters
            
        Returns:
            str: Unique cache key
        """
        # Create a string representation of the request
        key_data = {
            'endpoint': endpoint,
            'params': params or {}
        }
        
        # Sort parameters for consistent key generation
        key_string = json.dumps(key_data, sort_keys=True)
        
        # Generate hash for shorter, consistent keys
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{prefix}{endpoint}:{key_hash}"
    
    def _serialize_data(self, data: Any) -> str:
        """
        Serialize data for Redis storage.
        
        Args:
            data: Data to serialize
            
        Returns:
            str: Serialized data
        """
        cache_data = {
            'data': data,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'cached': True
        }
        return json.dumps(cache_data)
    
    def _deserialize_data(self, serialized_data: str) -> Dict[str, Any]:
        """
        Deserialize data from Redis storage.
        
        Args:
            serialized_data: Serialized data string
            
        Returns:
            Dict: Deserialized data with metadata
        """
        try:
            return json.loads(serialized_data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize cache data: {e}")
            return None
    
    def get_short_cache(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Get data from short-term cache.
        
        Args:
            endpoint: API endpoint name
            params: Request parameters
            
        Returns:
            Dict: Cached data with metadata or None if not found
        """
        if not is_redis_available():
            logger.warning("Redis not available for short cache retrieval")
            return None
        
        try:
            redis_client = get_redis_client()
            cache_key = self._generate_cache_key(self.short_cache_prefix, endpoint, params)
            
            cached_data = redis_client.get(cache_key)
            if cached_data:
                deserialized = self._deserialize_data(cached_data)
                if deserialized:
                    deserialized['cached'] = 'short_term'
                    logger.info(f"Short cache hit for {endpoint}")
                    return deserialized
            
            logger.debug(f"Short cache miss for {endpoint}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving from short cache: {e}")
            return None
    
    def set_short_cache(self, endpoint: str, data: Any, params: Dict[str, Any] = None) -> bool:
        """
        Store data in short-term cache.
        
        Args:
            endpoint: API endpoint name
            data: Data to cache
            params: Request parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not is_redis_available():
            logger.warning("Redis not available for short cache storage")
            return False
        
        try:
            redis_client = get_redis_client()
            cache_key = self._generate_cache_key(self.short_cache_prefix, endpoint, params)
            serialized_data = self._serialize_data(data)
            
            redis_client.setex(cache_key, self.short_cache_ttl, serialized_data)
            logger.info(f"Data cached in short cache for {endpoint} (TTL: {self.short_cache_ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error storing in short cache: {e}")
            return False
    
    def get_fallback_cache(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Get data from fallback cache.
        
        Args:
            endpoint: API endpoint name
            params: Request parameters
            
        Returns:
            Dict: Cached data with metadata or None if not found
        """
        if not is_redis_available():
            logger.warning("Redis not available for fallback cache retrieval")
            return None
        
        try:
            redis_client = get_redis_client()
            cache_key = self._generate_cache_key(self.fallback_cache_prefix, endpoint, params)
            
            cached_data = redis_client.get(cache_key)
            if cached_data:
                deserialized = self._deserialize_data(cached_data)
                if deserialized:
                    deserialized['cached'] = 'fallback'
                    logger.info(f"Fallback cache hit for {endpoint}")
                    return deserialized
            
            logger.debug(f"Fallback cache miss for {endpoint}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving from fallback cache: {e}")
            return None
    
    def set_fallback_cache(self, endpoint: str, data: Any, params: Dict[str, Any] = None) -> bool:
        """
        Store data in fallback cache.
        
        Args:
            endpoint: API endpoint name
            data: Data to cache
            params: Request parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not is_redis_available():
            logger.warning("Redis not available for fallback cache storage")
            return False
        
        try:
            redis_client = get_redis_client()
            cache_key = self._generate_cache_key(self.fallback_cache_prefix, endpoint, params)
            serialized_data = self._serialize_data(data)
            
            redis_client.setex(cache_key, self.fallback_cache_ttl, serialized_data)
            logger.info(f"Data cached in fallback cache for {endpoint} (TTL: {self.fallback_cache_ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error storing in fallback cache: {e}")
            return False
    
    def clear_cache(self, endpoint: str = None, cache_type: str = "all") -> bool:
        """
        Clear cache data.
        
        Args:
            endpoint: Specific endpoint to clear (None for all)
            cache_type: Type of cache to clear ("short", "fallback", or "all")
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not is_redis_available():
            logger.warning("Redis not available for cache clearing")
            return False
        
        try:
            redis_client = get_redis_client()
            
            patterns = []
            if cache_type in ["short", "all"]:
                pattern = f"{self.short_cache_prefix}{endpoint or '*'}:*"
                patterns.append(pattern)
            
            if cache_type in ["fallback", "all"]:
                pattern = f"{self.fallback_cache_prefix}{endpoint or '*'}:*"
                patterns.append(pattern)
            
            cleared_count = 0
            for pattern in patterns:
                keys = redis_client.keys(pattern)
                if keys:
                    cleared_count += redis_client.delete(*keys)
            
            logger.info(f"Cleared {cleared_count} cache entries")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict: Cache statistics
        """
        if not is_redis_available():
            return {"error": "Redis not available"}
        
        try:
            redis_client = get_redis_client()
            
            short_keys = redis_client.keys(f"{self.short_cache_prefix}*")
            fallback_keys = redis_client.keys(f"{self.fallback_cache_prefix}*")
            
            return {
                "redis_available": True,
                "short_cache_entries": len(short_keys),
                "fallback_cache_entries": len(fallback_keys),
                "total_entries": len(short_keys) + len(fallback_keys),
                "short_cache_ttl": self.short_cache_ttl,
                "fallback_cache_ttl": self.fallback_cache_ttl
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)} 