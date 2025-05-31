from flask import request, jsonify
from utils import build_url, validate_parameters, get_content_with_cache

def handle_comercializacao(cache_manager, logger):
    """Handles the logic for the /comercializacao endpoint."""
    route_name = 'comercializacao'
    year = request.args.get('year')
    sub_option = request.args.get('sub_option')
    
    is_valid, error_message = validate_parameters(year, sub_option, route_name)
    if not is_valid:
        return jsonify({"error": error_message}), 400
    
    url = build_url(route_name, year, sub_option)
    params = {'year': year, 'sub_option': sub_option}
    
    content, cached_flag = get_content_with_cache(route_name, url, cache_manager, logger, params)
    
    if content is None:
        return jsonify({"error": "Failed to fetch data and no cache available"}), 500
    
    response_data = content.copy() if isinstance(content, dict) else {"data": content}
    response_data["cached"] = cached_flag
    return jsonify(response_data), 200 