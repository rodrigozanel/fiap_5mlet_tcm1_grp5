from flask import request, jsonify
from utils import build_url, validate_parameters, get_content_with_cache
import logging

def handle_producao(cache_manager, logger):
    """
    Handles the logic for the /producao endpoint with robust error handling.
    
    Implements comprehensive error handling to prevent 500 errors and provide
    informative responses even when all cache layers fail.
    """
    route_name = 'producao'
    
    try:
        # Get and validate parameters
        year = request.args.get('year')
        sub_option = request.args.get('sub_option')
        
        logger.info(f"📊 Processing {route_name} request: year={year}, sub_option={sub_option}")
        
        # Validate parameters
        is_valid, error_message = validate_parameters(year, sub_option, route_name)
        if not is_valid:
            logger.warning(f"❌ Parameter validation failed for {route_name}: {error_message}")
            return jsonify({
                "error": error_message,
                "endpoint": route_name,
                "provided_params": {"year": year, "sub_option": sub_option},
                "status": "parameter_error"
            }), 400
        
        # Build URL and prepare parameters
        try:
            url = build_url(route_name, year, sub_option)
            params = {'year': year, 'sub_option': sub_option}
            logger.debug(f"🔗 Built URL for {route_name}: {url}")
        except Exception as url_error:
            logger.error(f"❌ URL building failed for {route_name}: {url_error}")
            return jsonify({
                "error": "Failed to build request URL",
                "details": str(url_error),
                "endpoint": route_name,
                "status": "url_error"
            }), 400
        
        # Attempt to get content with comprehensive fallback chain
        logger.info(f"🚀 Initiating data retrieval for {route_name}")
        content, cached_flag = get_content_with_cache(route_name, url, cache_manager, logger, params)
        
        if content is None:
            # All layers failed - provide informative error response
            logger.error(f"💥 All data sources failed for {route_name}")
            
            # Get cache statistics for debugging
            try:
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
                "requested_params": {"year": year, "sub_option": sub_option},
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
                "timestamp": cache_stats.get("timestamp", "unknown")
            }), 503  # Service Unavailable - more appropriate than 500
        
        # Successful data retrieval
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
            
            # Add helpful metadata
            if cached_flag:
                if cached_flag == 'csv_fallback':
                    response_data["data_source"] = "Local CSV files (Redis unavailable)"
                    response_data["freshness"] = "Static data from local files"
                elif cached_flag in ['short_term', 'fallback']:
                    response_data["data_source"] = f"Redis {cached_flag} cache"
                    response_data["freshness"] = "Cached data"
            else:
                response_data["data_source"] = "Fresh web scraping"
                response_data["freshness"] = "Real-time data"
            
            logger.info(f"✅ Successfully served {route_name} data (source: {response_data.get('data_source', 'unknown')})")
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
    
    except Exception as e:
        # Catch-all error handler to prevent unhandled exceptions
        logger.critical(f"💥 CRITICAL ERROR in {route_name} handler: {e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": "An unexpected error occurred while processing your request",
            "endpoint": route_name,
            "status": "critical_error",
            "troubleshooting": {
                "suggestion": "Please try again later or contact support if the issue persists"
            }
        }), 500 