from flask import request, jsonify
from utils import get_content_with_cache, build_url, validate_parameters
from .handler_utils import format_success_response, format_error_response, format_service_unavailable_response

def handle_producao(cache_manager, logger):
    """
    Handler for producao endpoint with comprehensive error handling and validation.
    
    Returns structured JSON response with year and TTL information.
    """
    route_name = "producao"
    logger.info(f"🎯 Processing {route_name} request")
    
    try:
        # Extract and validate parameters
        year = request.args.get('year')
        sub_option = request.args.get('sub_option')
        
        # Validate parameters
        is_valid, error_message = validate_parameters(year, sub_option, route_name)
        if not is_valid:
            logger.warning(f"⚠️ Parameter validation failed for {route_name}: {error_message}")
            return format_error_response(
                route_name=route_name,
                error_message=error_message,
                provided_params={"year": year, "sub_option": sub_option}
            )
        
        # Build URL for web scraping
        url = build_url(route_name, year, sub_option)
        logger.debug(f"Built URL for {route_name}: {url}")
        
        # Prepare parameters for cache key generation
        params = {"year": year, "sub_option": sub_option}
        
        # Fetch content with three-layer cache strategy
        content, cached_flag = get_content_with_cache(route_name, url, cache_manager, logger, params)
        
        # Handle data retrieval failure
        if content is None:
            logger.error(f"❌ All data sources failed for {route_name}")
            return format_service_unavailable_response(
                route_name=route_name,
                cache_manager=cache_manager,
                logger=logger,
                requested_params=params
            )
        
        # Successful data retrieval - use utility function for consistent formatting
        return format_success_response(content, cached_flag, route_name, logger)
        
    except Exception as e:
        # Critical error handling
        logger.critical(f"💥 Critical error in {route_name} handler: {e}", exc_info=True)
        return format_error_response(
            route_name=route_name,
            error_message="Internal server error",
            status_code=500,
            error_type="internal_error",
            technical_details=str(e)
        ) 