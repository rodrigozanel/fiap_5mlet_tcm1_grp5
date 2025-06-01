"""
Utility functions for API handlers
"""

from flask import jsonify

def format_success_response(content, cached_flag, route_name, logger):
    """
    Format a successful API response with year, TTL, and cache information.
    
    Args:
        content: The response content/data
        cached_flag: Cache flag indicating source
        route_name: Name of the API endpoint
        logger: Logger instance
        
    Returns:
        tuple: (jsonify response, status_code)
    """
    try:
        # Prepare response data
        if isinstance(content, dict):
            response_data = content.copy()
        else:
            response_data = {"data": content}
        
        # Add cache metadata
        response_data["cached"] = cached_flag
        response_data["endpoint"] = route_name
        response_data["status"] = "success"
        
        # Extract and add year and TTL information to top level for easy access
        metadata = response_data.get('metadata', {})
        
        # Add year to top level
        response_data["year"] = metadata.get('year', 'unknown')
        
        # Ensure year is never None
        if response_data["year"] is None or response_data["year"] == "":
            response_data["year"] = "unknown"
        
        # Add TTL information to top level in user-friendly format
        cache_ttl = metadata.get('cache_ttl', {})
        response_data["cache_info"] = {
            "active_cache_layer": metadata.get('cache_status', {}).get('active_layer', 'unknown'),
            "layer_description": metadata.get('cache_status', {}).get('layer_description', 'Unknown'),
            "ttl_seconds": {
                "short_cache": cache_ttl.get('short_cache_ttl'),
                "fallback_cache": cache_ttl.get('fallback_cache_ttl'),
                "csv_fallback": cache_ttl.get('csv_fallback_ttl', 'indefinite')
            }
        }
        
        # Add helpful metadata
        if cached_flag:
            if cached_flag == 'csv_fallback':
                response_data["data_source"] = "Local CSV files (Redis unavailable)"
                response_data["freshness"] = "Static data from local files"
                response_data["cache_expires_in"] = "N/A (indefinite)"
            elif cached_flag in ['short_term', 'fallback']:
                response_data["data_source"] = f"Redis {cached_flag} cache"
                response_data["freshness"] = "Cached data"
                
                # Add TTL in human readable format for cached data
                # Use the correct TTL key based on cache type
                ttl_key = 'short_cache_ttl' if cached_flag == 'short_term' else 'fallback_cache_ttl'
                ttl_seconds = cache_ttl.get(ttl_key)
                
                if ttl_seconds and isinstance(ttl_seconds, int) and ttl_seconds > 0:
                    hours = ttl_seconds // 3600
                    minutes = (ttl_seconds % 3600) // 60
                    seconds = ttl_seconds % 60
                    
                    if hours > 0:
                        response_data["cache_expires_in"] = f"{hours}h {minutes}m {seconds}s"
                    elif minutes > 0:
                        response_data["cache_expires_in"] = f"{minutes}m {seconds}s"
                    else:
                        response_data["cache_expires_in"] = f"{seconds}s"
                else:
                    # Fallback: show the raw TTL value or unknown
                    if ttl_seconds == "redis_unavailable":
                        response_data["cache_expires_in"] = "Redis unavailable"
                    elif ttl_seconds == "no_expiry":
                        response_data["cache_expires_in"] = "No expiry set"
                    else:
                        response_data["cache_expires_in"] = f"TTL: {ttl_seconds}"
        else:
            response_data["data_source"] = "Fresh web scraping"
            response_data["freshness"] = "Real-time data"
            response_data["cache_expires_in"] = "N/A (fresh data)"
        
        logger.info(f"✅ Successfully served {route_name} data for year {response_data['year']} (source: {response_data.get('data_source', 'unknown')})")
        return jsonify(response_data), 200
        
    except Exception as response_error:
        logger.error(f"❌ Failed to prepare response for {route_name}: {response_error}")
        return jsonify({
            "error": "Response preparation failed",
            "message": "Data was retrieved but failed to format response",
            "endpoint": route_name,
            "status": "response_error",
            "cached": cached_flag
        }), 500

def format_error_response(route_name, error_message, status_code=400, error_type="parameter_error", **kwargs):
    """
    Format a standardized error response.
    
    Args:
        route_name: Name of the API endpoint
        error_message: Error message to return
        status_code: HTTP status code (default 400)
        error_type: Type of error for categorization
        **kwargs: Additional fields to include in response
        
    Returns:
        tuple: (jsonify response, status_code)
    """
    error_response = {
        "error": error_message,
        "endpoint": route_name,
        "status": error_type,
        **kwargs
    }
    
    return jsonify(error_response), status_code

def format_service_unavailable_response(route_name, cache_manager, logger, **kwargs):
    """
    Format a service unavailable response when all data sources fail.
    
    Args:
        route_name: Name of the API endpoint
        cache_manager: Cache manager instance
        logger: Logger instance
        **kwargs: Additional fields like requested_params
        
    Returns:
        tuple: (jsonify response, status_code)
    """
    try:
        # Get cache statistics for debugging
        cache_stats = cache_manager.get_cache_stats()
        csv_validation = cache_manager.validate_csv_fallback() if cache_manager.csv_fallback else None
    except Exception as stats_error:
        logger.warning(f"⚠️ Failed to get cache stats: {stats_error}")
        cache_stats = {"error": "Stats unavailable"}
        csv_validation = None
    
    return jsonify({
        "error": "Data temporarily unavailable",
        "message": "All data sources (web scraping, cache, and local files) are currently unavailable. Please try again later.",
        "endpoint": route_name,
        "status": "data_unavailable",
        "troubleshooting": {
            "retry_suggestion": "Try again in a few minutes",
            "alternative_years": "Try different year parameters",
            "contact_support": "If the issue persists, contact support"
        },
        "system_status": {
            "cache_health": cache_stats.get("overall_status", {}).get("health", "unknown"),
            "csv_fallback_status": csv_validation.get("overall_status") if csv_validation else "unavailable"
        },
        "timestamp": cache_stats.get("timestamp", "unknown"),
        **kwargs
    }), 503 