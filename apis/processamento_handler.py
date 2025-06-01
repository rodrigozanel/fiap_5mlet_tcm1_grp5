from flask import request, jsonify
from utils import build_url, validate_parameters, get_content_with_cache
from .handler_utils import format_success_response, format_error_response, format_service_unavailable_response

def handle_processamento(cache_manager, logger):
    """
    Handler for processamento endpoint with comprehensive error handling and validation.
    
    Returns structured JSON response with year and TTL information.
    """
    route_name = "processamento"
    logger.info(f"🎯 Processing {route_name} request")
    
    try:
        # Extract and validate parameters
        year = request.args.get('year')
        sub_option = request.args.get('sub_option')
        
        # Validate parameters
        is_valid, error_message = validate_parameters(year, sub_option, route_name)
        if not is_valid:
            logger.warning(f"⚠️ Parameter validation failed for {route_name}: {error_message}")
            return format_error_response(route_name, error_message, 400, "parameter_error")
        
        # Build URL and prepare parameters
        url = build_url(route_name, year, sub_option)
        params = {'year': year, 'sub_option': sub_option}
        
        logger.info(f"🌐 Fetching data for {route_name} from {url}")
        
        # Get content using three-layer cache strategy
        content, cached_flag = get_content_with_cache(route_name, url, cache_manager, logger, params)
        
        if content is None:
            logger.error(f"❌ All data sources failed for {route_name}")
            return format_service_unavailable_response(
                route_name, 
                cache_manager, 
                logger,
                requested_params=params
            )
        
        # Return successful response with all metadata
        return format_success_response(content, cached_flag, route_name, logger)
        
    except Exception as e:
        logger.error(f"❌ Unexpected error in {route_name} handler: {e}", exc_info=True)
        return format_error_response(
            route_name, 
            "An unexpected error occurred while processing the request", 
            500, 
            "internal_error",
            exception_type=type(e).__name__
        ) 