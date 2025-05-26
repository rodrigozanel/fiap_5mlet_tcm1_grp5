"""
Cache module for Flask Web Scraping API
Provides Redis-based caching functionality with short-term and fallback cache layers.
"""

from .redis_client import get_redis_client
from .cache_manager import CacheManager

__all__ = ['get_redis_client', 'CacheManager'] 