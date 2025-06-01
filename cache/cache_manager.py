"""
Cache manager for handling short-term, fallback, and CSV fallback caching strategies.
"""

import os
import json
import hashlib
import logging
from typing import Any, Optional, Dict, Union
from datetime import datetime, timezone

from .redis_client import get_redis_client, is_redis_available
from .csv_fallback import CsvFallbackManager

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages three-layer caching system:
    1. Short-term cache: For HTTP request responses (default: 5 minutes)
    2. Fallback cache: For web scraping data when source is unavailable (default: 30 days)
    3. CSV fallback: For local CSV files when Redis is unavailable (file-based)
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
        
        # Initialize CSV fallback manager
        csv_directory = os.getenv('CSV_FALLBACK_DIR', 'data/fallback')
        try:
            self.csv_fallback = CsvFallbackManager(
                csv_directory=csv_directory,
                cache_enabled=True,
                max_cache_size=50,  # Moderate cache size for production
                cache_ttl_seconds=1800  # 30 minutes cache TTL for CSV data
            )
            logger.info(f"CSV fallback initialized with directory: {csv_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize CSV fallback: {e}")
            self.csv_fallback = None
    
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
        Get data from short-term cache with enhanced logging.
        
        Args:
            endpoint: API endpoint name
            params: Request parameters
            
        Returns:
            Dict: Cached data with metadata or None if not found
        """
        if not is_redis_available():
            logger.warning(f"🔴 Redis unavailable for short cache retrieval of {endpoint}")
            return None
        
        try:
            redis_client = get_redis_client()
            cache_key = self._generate_cache_key(self.short_cache_prefix, endpoint, params)
            
            logger.debug(f"🔍 Checking short cache for {endpoint} (key: {cache_key})")
            
            cached_data = redis_client.get(cache_key)
            if cached_data:
                deserialized = self._deserialize_data(cached_data)
                if deserialized:
                    deserialized['cached'] = 'short_term'
                    logger.info(f"🎯 Short cache HIT for {endpoint} (TTL: {self.short_cache_ttl}s)")
                    return deserialized
                else:
                    logger.warning(f"⚠️ Short cache data corrupted for {endpoint} - failed to deserialize")
            
            logger.debug(f"🎯 Short cache MISS for {endpoint}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Short cache retrieval ERROR for {endpoint}: {e}", exc_info=True)
            return None
    
    def set_short_cache(self, endpoint: str, data: Any, params: Dict[str, Any] = None) -> bool:
        """
        Store data in short-term cache with enhanced logging.
        
        Args:
            endpoint: API endpoint name
            data: Data to cache
            params: Request parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not is_redis_available():
            logger.warning(f"🔴 Redis unavailable for short cache storage of {endpoint}")
            return False
        
        try:
            redis_client = get_redis_client()
            cache_key = self._generate_cache_key(self.short_cache_prefix, endpoint, params)
            serialized_data = self._serialize_data(data)
            
            redis_client.setex(cache_key, self.short_cache_ttl, serialized_data)
            
            # Log storage info
            data_size = len(serialized_data) if serialized_data else 0
            logger.info(f"💾 Short cache STORED for {endpoint} (TTL: {self.short_cache_ttl}s, Size: {data_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Short cache storage ERROR for {endpoint}: {e}", exc_info=True)
            return False
    
    def get_fallback_cache(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Get data from fallback cache with enhanced logging.
        
        Args:
            endpoint: API endpoint name
            params: Request parameters
            
        Returns:
            Dict: Cached data with metadata or None if not found
        """
        if not is_redis_available():
            logger.warning(f"🔴 Redis unavailable for fallback cache retrieval of {endpoint}")
            return None
        
        try:
            redis_client = get_redis_client()
            cache_key = self._generate_cache_key(self.fallback_cache_prefix, endpoint, params)
            
            logger.debug(f"🔍 Checking fallback cache for {endpoint} (key: {cache_key})")
            
            cached_data = redis_client.get(cache_key)
            if cached_data:
                deserialized = self._deserialize_data(cached_data)
                if deserialized:
                    deserialized['cached'] = 'fallback'
                    
                    # Calculate age of cached data
                    try:
                        cache_timestamp = deserialized.get('timestamp')
                        if cache_timestamp:
                            from datetime import datetime
                            cached_time = datetime.fromisoformat(cache_timestamp.replace('Z', '+00:00'))
                            age_seconds = (datetime.now(timezone.utc) - cached_time).total_seconds()
                            age_hours = age_seconds / 3600
                            logger.info(f"🕰️ Fallback cache HIT for {endpoint} (Age: {age_hours:.1f}h)")
                        else:
                            logger.info(f"🕰️ Fallback cache HIT for {endpoint} (Age: unknown)")
                    except Exception:
                        logger.info(f"🕰️ Fallback cache HIT for {endpoint}")
                    
                    return deserialized
                else:
                    logger.warning(f"⚠️ Fallback cache data corrupted for {endpoint} - failed to deserialize")
            
            logger.debug(f"🕰️ Fallback cache MISS for {endpoint}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Fallback cache retrieval ERROR for {endpoint}: {e}", exc_info=True)
            return None
    
    def set_fallback_cache(self, endpoint: str, data: Any, params: Dict[str, Any] = None) -> bool:
        """
        Store data in fallback cache with enhanced logging.
        
        Args:
            endpoint: API endpoint name
            data: Data to cache
            params: Request parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not is_redis_available():
            logger.warning(f"🔴 Redis unavailable for fallback cache storage of {endpoint}")
            return False
        
        try:
            redis_client = get_redis_client()
            cache_key = self._generate_cache_key(self.fallback_cache_prefix, endpoint, params)
            serialized_data = self._serialize_data(data)
            
            redis_client.setex(cache_key, self.fallback_cache_ttl, serialized_data)
            
            # Log storage info with TTL in human readable format
            data_size = len(serialized_data) if serialized_data else 0
            ttl_days = self.fallback_cache_ttl / 86400
            logger.info(f"💾 Fallback cache STORED for {endpoint} (TTL: {ttl_days:.0f} days, Size: {data_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fallback cache storage ERROR for {endpoint}: {e}", exc_info=True)
            return False
    
    def get_csv_fallback(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Get data from CSV fallback (third layer) with enhanced logging.
        
        Args:
            endpoint: API endpoint name
            params: Request parameters (including sub_option, year, etc.)
            
        Returns:
            Dict: CSV data converted to API format with metadata or None if not found
        """
        if not self.csv_fallback:
            logger.warning(f"🚫 CSV fallback unavailable for {endpoint} - not initialized")
            return None
        
        try:
            # Extract parameters for CSV fallback
            sub_option = params.get('sub_option') if params else None
            year = params.get('year') if params else None
            
            logger.info(f"🗂️ Attempting CSV fallback for {endpoint} (sub_option: {sub_option}, year: {year})")
            
            # Get data from CSV fallback
            csv_data = self.csv_fallback.get_data_for_endpoint(
                endpoint=endpoint,
                sub_option=sub_option,
                year=year
            )
            
            if csv_data:
                # Add cache metadata to match other cache layers
                csv_data['cached'] = 'csv_fallback'
                csv_data['timestamp'] = datetime.now(timezone.utc).isoformat()
                
                # Log successful CSV fallback with data info
                data_info = ""
                if csv_data.get('data', {}).get('body'):
                    body_rows = len(csv_data['data']['body'])
                    data_info = f" ({body_rows} rows)"
                
                logger.info(f"✅ CSV fallback SUCCESS for {endpoint}{data_info} (sub_option: {sub_option})")
                return csv_data
            else:
                logger.warning(f"🗂️ CSV fallback MISS for {endpoint} - no matching data (sub_option: {sub_option})")
                return None
                
        except Exception as e:
            logger.error(f"❌ CSV fallback ERROR for {endpoint}: {e}", exc_info=True)
            
            # Try to get more context about the error
            error_context = {
                'endpoint': endpoint,
                'sub_option': sub_option,
                'year': year,
                'csv_manager_available': self.csv_fallback is not None
            }
            
            # Check if it's a specific CSV error type
            if hasattr(e, '__class__'):
                error_context['error_type'] = e.__class__.__name__
            
            logger.error(f"🔍 CSV fallback error context: {error_context}")
            return None
    
    def get_csv_fallback_stats(self) -> Dict[str, Any]:
        """
        Get CSV fallback cache statistics.
        
        Returns:
            Dict: CSV fallback statistics or error info
        """
        if not self.csv_fallback:
            return {"csv_fallback_available": False, "message": "CSV fallback not initialized"}
        
        try:
            return self.csv_fallback.get_cache_stats()
        except Exception as e:
            logger.error(f"Error getting CSV fallback stats: {e}")
            return {"csv_fallback_available": False, "error": str(e)}
    
    def validate_csv_fallback(self) -> Dict[str, Any]:
        """
        Validate CSV fallback configuration and available files.
        
        Returns:
            Dict: Validation report for CSV fallback system
        """
        if not self.csv_fallback:
            return {
                "csv_fallback_available": False,
                "message": "CSV fallback not initialized"
            }
        
        try:
            return self.csv_fallback.validate_endpoint_mapping()
        except Exception as e:
            logger.error(f"Error validating CSV fallback: {e}")
            return {
                "csv_fallback_available": False,
                "error": str(e)
            }
    
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
        Get comprehensive cache statistics for all three layers.
        
        Returns:
            Dict: Complete cache statistics including Redis and CSV fallback
        """
        stats = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cache_layers": {
                "short_term": {},
                "fallback": {},
                "csv_fallback": {}
            }
        }
        
        # Redis-based cache statistics
        if is_redis_available():
            try:
                redis_client = get_redis_client()
                
                short_keys = redis_client.keys(f"{self.short_cache_prefix}*")
                fallback_keys = redis_client.keys(f"{self.fallback_cache_prefix}*")
                
                stats["redis_available"] = True
                stats["cache_layers"]["short_term"] = {
                    "entries": len(short_keys),
                    "ttl_seconds": self.short_cache_ttl,
                    "status": "active"
                }
                stats["cache_layers"]["fallback"] = {
                    "entries": len(fallback_keys),
                    "ttl_seconds": self.fallback_cache_ttl,
                    "status": "active"
                }
                stats["total_redis_entries"] = len(short_keys) + len(fallback_keys)
                
            except Exception as e:
                logger.error(f"Error getting Redis cache stats: {e}")
                stats["redis_available"] = False
                stats["redis_error"] = str(e)
                stats["cache_layers"]["short_term"]["status"] = "error"
                stats["cache_layers"]["fallback"]["status"] = "error"
        else:
            stats["redis_available"] = False
            stats["cache_layers"]["short_term"]["status"] = "unavailable"
            stats["cache_layers"]["fallback"]["status"] = "unavailable"
        
        # CSV fallback statistics
        if self.csv_fallback:
            try:
                csv_stats = self.csv_fallback.get_cache_stats()
                stats["cache_layers"]["csv_fallback"] = {
                    "status": "active",
                    "cache_enabled": csv_stats.get("cache_enabled", False),
                    "entries": csv_stats.get("current_size", 0),
                    "max_size": csv_stats.get("max_size", 0),
                    "hit_rate_percent": csv_stats.get("hit_rate_percent", 0),
                    "total_requests": csv_stats.get("total_requests", 0),
                    "cache_efficiency": csv_stats.get("cache_efficiency", "unknown"),
                    "ttl_seconds": csv_stats.get("ttl_seconds", 0)
                }
                
                # Add CSV fallback validation
                validation = self.csv_fallback.validate_endpoint_mapping()
                stats["csv_fallback_validation"] = {
                    "overall_status": validation.get("overall_status", "unknown"),
                    "total_endpoints": validation.get("total_endpoints", 0),
                    "valid_endpoints": validation.get("valid_endpoints", 0),
                    "existing_files": validation.get("existing_files", 0),
                    "missing_files": validation.get("missing_files", 0)
                }
                
            except Exception as e:
                logger.error(f"Error getting CSV fallback stats: {e}")
                stats["cache_layers"]["csv_fallback"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            stats["cache_layers"]["csv_fallback"] = {
                "status": "not_initialized"
            }
        
        # Overall cache health
        active_layers = sum(1 for layer in stats["cache_layers"].values() 
                          if layer.get("status") == "active")
        stats["overall_status"] = {
            "active_layers": active_layers,
            "total_layers": 3,
            "health": "excellent" if active_layers == 3 else "good" if active_layers >= 2 else "fair" if active_layers == 1 else "poor"
        }
        
        return stats 