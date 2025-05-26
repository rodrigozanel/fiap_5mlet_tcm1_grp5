import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from flasgger import Swagger
import urllib.parse
import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import cache modules
from cache import CacheManager

# Import version management
def get_version_info():
    """Get version information from various sources"""
    # Try Docker environment variables first
    if os.getenv('APP_VERSION'):
        return {
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'build_date': os.getenv('APP_BUILD_DATE', datetime.now().isoformat()),
            'environment': os.getenv('APP_ENVIRONMENT', 'production'),
            'source': 'docker'
        }
    
    # Try simple version file
    try:
        from simple_version import get_version_info as get_simple_version
        info = get_simple_version()
        info['environment'] = 'local'
        info['source'] = 'file'
        return info
    except ImportError:
        # Final fallback
        return {
            'version': "1.0.0",
            'build_date': datetime.now().isoformat(),
            'environment': 'unknown',
            'source': 'fallback'
        }

VERSION_INFO = get_version_info()
APP_VERSION = VERSION_INFO['version']

app = Flask(__name__)

# Initialize cache manager
cache_manager = CacheManager()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app.config['SWAGGER'] = {
    'title': 'Flask Web Scraping API - Dados Vitivinícolas Embrapa',
    'uiversion': 3,
    'description': f'API para extração de dados vitivinícolas do site da Embrapa via web scraping\n\nVersão: {VERSION_INFO["version"]}\nAmbiente: {VERSION_INFO["environment"]}\nData: {VERSION_INFO["build_date"]}',
    'version': APP_VERSION,
    'termsOfService': '',
    'contact': {
        'name': 'API Support',
        'url': 'http://localhost:5000',
        'email': 'support@example.com'
    },
    'license': {
        'name': 'MIT',
        'url': 'https://opensource.org/licenses/MIT'
    },
    'host': 'localhost:5000',
    'basePath': '/',
    'schemes': ['http'],
    'securityDefinitions': {
        'BasicAuth': {
            'type': 'basic'
        }
    },
    'security': [
        {
            'BasicAuth': []
        }
    ]
}

swagger = Swagger(app, template={
    'swagger': '2.0',
    'info': {
        'title': app.config['SWAGGER']['title'],
        'description': app.config['SWAGGER']['description'],
        'version': app.config['SWAGGER']['version']
    },
    'securityDefinitions': app.config['SWAGGER']['securityDefinitions'],
    'security': app.config['SWAGGER']['security']
})

auth = HTTPBasicAuth()

users = {
    "user1": "password1",
    "user2": "password2"
}

baseURL = "http://vitibrasil.cnpuv.embrapa.br/index.php"

# Mapping between route names and their corresponding 'opcao' values
ROUTE_OPCAO_MAP = {
    'production': 'opt_02',
    'processamento': 'opt_03',
    'comercializacao': 'opt_04',
    'importacao': 'opt_05',
    'exportacao': 'opt_06'
}

# Validation constants
VALID_YEARS = list(range(1970, 2025))  # 1970-2024
VALID_SUB_OPTIONS = {
    'production': ['VINHO DE MESA', 'VINHO FINO DE MESA (VINIFERA)', 'SUCO DE UVA', 'DERIVADOS'],
    'processamento': ['viniferas', 'americanas', 'mesa', 'semclass'],
    'comercializacao': ['VINHO DE MESA', 'ESPUMANTES', 'UVAS FRESCAS', 'SUCO DE UVA'],
    'importacao': ['vinhos', 'espumantes', 'frescas', 'passas', 'suco'],
    'exportacao': ['vinho', 'uva', 'espumantes', 'suco']
}

def validate_parameters(year=None, sub_option=None, endpoint=None):
    """
    Validate year and sub_option parameters.
    
    Args:
        year (str): Year parameter to validate
        sub_option (str): Sub-option parameter to validate
        endpoint (str): Endpoint name for sub_option validation
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Validate year
    if year is not None:
        try:
            year_int = int(year)
            if year_int not in VALID_YEARS:
                return False, f"Ano inválido. Deve estar entre {min(VALID_YEARS)} e {max(VALID_YEARS)}."
        except ValueError:
            return False, "Ano deve ser um número inteiro válido."
    
    # Validate sub_option
    if sub_option is not None and endpoint is not None:
        valid_options = VALID_SUB_OPTIONS.get(endpoint, [])
        if valid_options and sub_option not in valid_options:
            return False, f"Sub-opção inválida para {endpoint}. Opções válidas: {', '.join(valid_options)}"
    
    return True, None

def build_url(route_name, year=None, sub_option=None):
    """
    Build a URL with the appropriate 'opcao' parameter based on the route name.
    Optionally includes 'ano' (year) and 'subopcao' (sub_option) parameters if provided.

    Args:
        route_name (str): The name of the route function
        year (str, optional): The year to filter by. Defaults to None.
        sub_option (str, optional): The sub-option to filter by. Defaults to None.

    Returns:
        str: The complete URL with query parameters
    """
    opcao = ROUTE_OPCAO_MAP.get(route_name)
    if not opcao:
        raise ValueError(f"No 'opcao' mapping found for route: {route_name}")

    params = {'opcao': opcao}

    # Add year parameter if it has a value
    if year:
        params['ano'] = year

    # Add sub_option parameter if it has a value
    if sub_option:
        params['subopcao'] = sub_option

    return f"{baseURL}?{urllib.parse.urlencode(params)}"


@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username
    return None


@app.route("/", methods=["GET"])
def home():
    """
    Página inicial da API.
    ---
    responses:
      200:
        description: Informações básicas da API.
    """
    return jsonify({
        "message": "API Flask de Web Scraping - Dados Vitivinícolas Embrapa",
        "version": "1.0.0",
        "endpoints": [
            "/producao",
            "/processamento", 
            "/comercializacao",
            "/importacao",
            "/exportacao"
        ],
        "health_check": "/heartbeat",
        "test_endpoint": "/test",
        "documentation": "/apidocs/",
        "authentication": "HTTP Basic Auth required"
    }), 200


@app.route("/test", methods=["GET"])
def test():
    """
    Endpoint de teste simples.
    ---
    responses:
      200:
        description: Teste bem-sucedido.
    """
    return jsonify({"status": "OK", "message": "API funcionando corretamente!"}), 200


@app.route("/heartbeat", methods=["GET"])
def heartbeat():
    """
    Endpoint de heartbeat para monitoramento da saúde da API.
    ---
    tags:
      - Health Check
    responses:
      200:
        description: API está funcionando corretamente.
        schema:
          type: object
          properties:
            status:
              type: string
              example: "healthy"
            timestamp:
              type: string
              example: "2025-05-26T01:48:00Z"
            uptime:
              type: string
              example: "API is running"
            version:
              type: string
              example: "1.0.0.45"
            semantic_version:
              type: string
              example: "1.0.0-45-g1a2b3c4"
            service:
              type: string
              example: "Flask Web Scraping API"
            build_info:
              type: object
              properties:
                build_number:
                  type: integer
                  example: 45
                commit_hash:
                  type: string
                  example: "1a2b3c4"
                branch:
                  type: string
                  example: "main"
                commit_date:
                  type: string
                  example: "2025-01-26 10:30:00 -0300"
                build_date:
                  type: string
                  example: "2025-01-26T13:45:00.123456"
    """
    # Check Redis connection
    redis_status = "connected" if cache_manager.redis_client and cache_manager.redis_client.ping() else "disconnected"
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": "API is running",
        "version": VERSION_INFO['version'],
        "service": "Flask Web Scraping API - Dados Vitivinícolas Embrapa",
        "endpoints_available": 5,
        "authentication": "HTTP Basic Auth",
        "version_info": {
            "version": VERSION_INFO['version'],
            "build_date": VERSION_INFO['build_date'],
            "environment": VERSION_INFO['environment'],
            "source": VERSION_INFO['source']
        },
        "cache": {
            "redis_status": redis_status,
            "short_cache_ttl": cache_manager.short_cache_ttl,
            "fallback_cache_ttl": cache_manager.fallback_cache_ttl
        },
        "docker": {
            "running_in_docker": os.getenv('APP_VERSION') is not None,
            "container_environment": os.getenv('APP_ENVIRONMENT', 'production')
        }
    }), 200


@app.route("/producao", methods=["GET"])
@auth.login_required
def production():
    """
    Busca dados de produção.
    ---
    parameters:
      - name: year
        in: query
        type: integer
        minimum: 1970
        maximum: 2024
        required: false
        description: O ano para filtrar os dados (1970-2024).
      - name: sub_option
        in: query
        type: string
        required: false
        enum: ["VINHO DE MESA", "VINHO FINO DE MESA (VINIFERA)", "SUCO DE UVA", "DERIVADOS"]
        description: A sub-opção para filtrar os dados de produção.
    responses:
      200:
        description: Dados de produção recuperados com sucesso.
        schema:
          type: object
          properties:
            data:
              type: object
            cached:
              type: string
              enum: [false, "short_term", "fallback"]
              description: Indica se os dados vieram do cache
      400:
        description: Parâmetros inválidos.
        schema:
          type: object
          properties:
            error:
              type: string
              description: Mensagem de erro de validação
      401:
        description: Autenticação necessária.
      500:
        description: Erro interno do servidor.
    """
    route_name = request.endpoint
    year = request.args.get('year')
    sub_option = request.args.get('sub_option')
    
    # Validate parameters
    is_valid, error_message = validate_parameters(year, sub_option, route_name)
    if not is_valid:
        return jsonify({"error": error_message}), 400
    
    # Build URL and parameters for cache
    url = build_url(route_name, year, sub_option)
    params = {'year': year, 'sub_option': sub_option}
    
    # Get content with cache
    content, cached_flag = get_content_with_cache('producao', url, params)
    
    if content is None:
        return jsonify({"error": "Failed to fetch data and no cache available"}), 500
    
    # Add cache flag to response
    response_data = content.copy() if isinstance(content, dict) else {"data": content}
    response_data["cached"] = cached_flag
    
    return jsonify(response_data), 200


@app.route("/processamento", methods=["GET"])
@auth.login_required
def processamento():
    """
    Busca dados de processamento.
    ---
    parameters:
      - name: year
        in: query
        type: integer
        minimum: 1970
        maximum: 2024
        required: false
        description: O ano para filtrar os dados (1970-2024).
      - name: sub_option
        in: query
        type: string
        required: false
        enum: ["viniferas", "americanas", "mesa", "semclass"]
        description: A sub-opção para filtrar os dados de processamento.
    responses:
      200:
        description: Dados de processamento recuperados com sucesso.
        schema:
          type: object
          properties:
            data:
              type: object
            cached:
              type: string
              enum: [false, "short_term", "fallback"]
              description: Indica se os dados vieram do cache
      400:
        description: Parâmetros inválidos.
        schema:
          type: object
          properties:
            error:
              type: string
              description: Mensagem de erro de validação
      401:
        description: Autenticação necessária.
      500:
        description: Erro interno do servidor.
    """
    route_name = request.endpoint
    year = request.args.get('year')
    sub_option = request.args.get('sub_option')
    
    # Validate parameters
    is_valid, error_message = validate_parameters(year, sub_option, route_name)
    if not is_valid:
        return jsonify({"error": error_message}), 400
    
    # Build URL and parameters for cache
    url = build_url(route_name, year, sub_option)
    params = {'year': year, 'sub_option': sub_option}
    
    # Get content with cache
    content, cached_flag = get_content_with_cache('processamento', url, params)
    
    if content is None:
        return jsonify({"error": "Failed to fetch data and no cache available"}), 500
    
    # Add cache flag to response
    response_data = content.copy() if isinstance(content, dict) else {"data": content}
    response_data["cached"] = cached_flag
    
    return jsonify(response_data), 200


@app.route("/comercializacao", methods=["GET"])
@auth.login_required
def comercializacao():
    """
    Busca dados de comercialização.
    ---
    parameters:
      - name: year
        in: query
        type: integer
        minimum: 1970
        maximum: 2024
        required: false
        description: O ano para filtrar os dados (1970-2024).
      - name: sub_option
        in: query
        type: string
        required: false
        enum: ["VINHO DE MESA", "ESPUMANTES", "UVAS FRESCAS", "SUCO DE UVA"]
        description: A sub-opção para filtrar os dados de comercialização.
    responses:
      200:
        description: Dados de comercialização recuperados com sucesso.
        schema:
          type: object
          properties:
            data:
              type: object
            cached:
              type: string
              enum: [false, "short_term", "fallback"]
              description: Indica se os dados vieram do cache
      400:
        description: Parâmetros inválidos.
        schema:
          type: object
          properties:
            error:
              type: string
              description: Mensagem de erro de validação
      401:
        description: Autenticação necessária.
      500:
        description: Erro interno do servidor.
    """
    route_name = request.endpoint
    year = request.args.get('year')
    sub_option = request.args.get('sub_option')
    
    # Validate parameters
    is_valid, error_message = validate_parameters(year, sub_option, route_name)
    if not is_valid:
        return jsonify({"error": error_message}), 400
    
    # Build URL and parameters for cache
    url = build_url(route_name, year, sub_option)
    params = {'year': year, 'sub_option': sub_option}
    
    # Get content with cache
    content, cached_flag = get_content_with_cache('comercializacao', url, params)
    
    if content is None:
        return jsonify({"error": "Failed to fetch data and no cache available"}), 500
    
    # Add cache flag to response
    response_data = content.copy() if isinstance(content, dict) else {"data": content}
    response_data["cached"] = cached_flag
    
    return jsonify(response_data), 200


@app.route("/importacao", methods=["GET"])
@auth.login_required
def importacao():    
    """
    Busca dados de importação.
    ---
    parameters:
      - name: year
        in: query
        type: integer
        minimum: 1970
        maximum: 2024
        required: false
        description: O ano para filtrar os dados (1970-2024).
      - name: sub_option
        in: query
        type: string
        required: false
        enum: ["vinhos", "espumantes", "frescas", "passas", "suco"]
        description: A sub-opção para filtrar os dados de importação.
    responses:
      200:
        description: Dados de importação recuperados com sucesso.
        schema:
          type: object
          properties:
            data:
              type: object
            cached:
              type: string
              enum: [false, "short_term", "fallback"]
              description: Indica se os dados vieram do cache
      400:
        description: Parâmetros inválidos.
        schema:
          type: object
          properties:
            error:
              type: string
              description: Mensagem de erro de validação
      401:
        description: Autenticação necessária.
      500:
        description: Erro interno do servidor.
    """
    route_name = request.endpoint
    year = request.args.get('year')
    sub_option = request.args.get('sub_option')
    
    # Validate parameters
    is_valid, error_message = validate_parameters(year, sub_option, route_name)
    if not is_valid:
        return jsonify({"error": error_message}), 400
    
    # Build URL and parameters for cache
    url = build_url(route_name, year, sub_option)
    params = {'year': year, 'sub_option': sub_option}
    
    # Get content with cache
    content, cached_flag = get_content_with_cache('importacao', url, params)
    
    if content is None:
        return jsonify({"error": "Failed to fetch data and no cache available"}), 500
    
    # Add cache flag to response
    response_data = content.copy() if isinstance(content, dict) else {"data": content}
    response_data["cached"] = cached_flag
    
    return jsonify(response_data), 200


@app.route("/exportacao", methods=["GET"])
@auth.login_required
def exportacao():
    """
    Busca dados de exportação.
    ---
    parameters:
      - name: year
        in: query
        type: integer
        minimum: 1970
        maximum: 2024
        required: false
        description: O ano para filtrar os dados (1970-2024).
      - name: sub_option
        in: query
        type: string
        required: false
        enum: ["vinho", "uva", "espumantes", "suco"]
        description: A sub-opção para filtrar os dados de exportação.
    responses:
      200:
        description: Dados de exportação recuperados com sucesso.
        schema:
          type: object
          properties:
            data:
              type: object
            cached:
              type: string
              enum: [false, "short_term", "fallback"]
              description: Indica se os dados vieram do cache
      400:
        description: Parâmetros inválidos.
        schema:
          type: object
          properties:
            error:
              type: string
              description: Mensagem de erro de validação
      401:
        description: Autenticação necessária.
      500:
        description: Erro interno do servidor.
    """
    route_name = request.endpoint
    year = request.args.get('year')
    sub_option = request.args.get('sub_option')
    
    # Validate parameters
    is_valid, error_message = validate_parameters(year, sub_option, route_name)
    if not is_valid:
        return jsonify({"error": error_message}), 400
    
    # Build URL and parameters for cache
    url = build_url(route_name, year, sub_option)
    params = {'year': year, 'sub_option': sub_option}
    
    # Get content with cache
    content, cached_flag = get_content_with_cache('exportacao', url, params)
    
    if content is None:
        return jsonify({"error": "Failed to fetch data and no cache available"}), 500
    
    # Add cache flag to response
    response_data = content.copy() if isinstance(content, dict) else {"data": content}
    response_data["cached"] = cached_flag
    
    return jsonify(response_data), 200


# Helper functions for parsing table data
def _parse_html_table_section(section_tag):
    """Parses rows and cells from a table section (thead, tbody, tfoot)."""
    rows_data = []
    if not section_tag:
        return rows_data
    for row_element in section_tag.find_all('tr'):
        current_row_cells = [
            cell_tag.get_text(strip=True)
            for cell_tag in row_element.find_all(['th', 'td'])
        ]
        if current_row_cells:
            rows_data.append(current_row_cells)
    return rows_data

def _parse_tbody_with_grouped_items(tbody_tag):
    """
    Parses a tbody element, grouping rows based on 'tb_item' and 'tb_subitem' classes.
    Rows not matching this structure are collected into a default group.
    """
    body_data_list = []
    if not tbody_tag:
        return body_data_list

    all_rows_in_tbody = tbody_tag.find_all('tr', recursive=False)
    current_row_index = 0
    default_group_for_ungrouped_rows = None

    while current_row_index < len(all_rows_in_tbody):
        current_tr_element = all_rows_in_tbody[current_row_index]
        td_elements = current_tr_element.find_all('td', limit=1)
        first_td_element = td_elements[0] if td_elements else None

        current_row_cells = [
            cell.get_text(strip=True)
            for cell in current_tr_element.find_all(['td', 'th'])
        ]

        if not current_row_cells: # Skip empty rows
            current_row_index += 1
            continue

        if first_td_element and 'tb_item' in first_td_element.get('class', []):
            current_item_group_dict = {"item_data": current_row_cells, "sub_items": []}
            body_data_list.append(current_item_group_dict)
            current_row_index += 1

            # Collect subsequent sub-items ('tb_subitem')
            while current_row_index < len(all_rows_in_tbody):
                potential_subitem_tr = all_rows_in_tbody[current_row_index]
                sub_td_elements = potential_subitem_tr.find_all('td', limit=1)
                first_td_of_subitem = sub_td_elements[0] if sub_td_elements else None

                if first_td_of_subitem and 'tb_subitem' in first_td_of_subitem.get('class', []):
                    sub_item_cells = [
                        cell.get_text(strip=True)
                        for cell in potential_subitem_tr.find_all(['td', 'th'])
                    ]
                    if sub_item_cells: # Only add if there's content
                        current_item_group_dict["sub_items"].append(sub_item_cells)
                    current_row_index += 1
                else:
                    break # Not a sub-item or end of rows for this group
        else:
            # Row is not a 'tb_item'; add to the default group
            if default_group_for_ungrouped_rows is None:
                # Initialize the default group if this is the first such row
                default_group_for_ungrouped_rows = {"item_data": [], "sub_items": []} 
                body_data_list.append(default_group_for_ungrouped_rows)
            
            # Add this row's data as a sub_item to the default group
            default_group_for_ungrouped_rows["sub_items"].append(current_row_cells)
            current_row_index += 1
            
    return body_data_list

def _parse_table_rows_fallback(table_tag, thead_tag, tfoot_tag):
    """
    Parses table rows that are not part of a thead or tfoot,
    used as a fallback when an explicit tbody is missing.
    """
    body_fallback_rows = []
    # Get all <tr> elements from thead and tfoot to exclude them
    thead_trs = set(thead_tag.find_all('tr')) if thead_tag else set()
    tfoot_trs = set(tfoot_tag.find_all('tr')) if tfoot_tag else set()

    for row_element in table_tag.find_all('tr'):
        # Process row if it's not in thead or tfoot
        if row_element not in thead_trs and row_element not in tfoot_trs:
            current_row_cells = [
                cell_tag.get_text(strip=True)
                for cell_tag in row_element.find_all(['td', 'th'])
            ]
            if current_row_cells: # Only add if there's actual content
                body_fallback_rows.append(current_row_cells)
    return body_fallback_rows

def get_content_with_cache(endpoint_name, url, params=None):
    """
    Fetch content with two-layer caching strategy.
    
    Args:
        endpoint_name (str): Name of the endpoint for cache key generation
        url (str): The URL to fetch content from
        params (dict): Request parameters for cache key generation
        
    Returns:
        tuple: (content, cached_flag) where cached_flag indicates cache source
    """
    try:
        # Try short-term cache first
        cached_response = cache_manager.get_short_cache(endpoint_name, params)
        if cached_response:
            logger.info(f"Returning data from short-term cache for {endpoint_name}")
            return cached_response['data'], cached_response['cached']
        
        # Try to fetch fresh data
        logger.info(f"Fetching fresh data from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse the content to get structured data
        parsed_data = parse_html_content(response.text)
        
        # Store in both caches
        cache_manager.set_short_cache(endpoint_name, parsed_data, params)
        cache_manager.set_fallback_cache(endpoint_name, parsed_data, params)
        
        logger.info(f"Fresh data fetched and cached for {endpoint_name}")
        return parsed_data, False
        
    except requests.RequestException as e:
        logger.error(f"Error fetching content from {url}: {e}")
        
        # Try fallback cache when web scraping fails
        cached_response = cache_manager.get_fallback_cache(endpoint_name, params)
        if cached_response:
            logger.warning(f"Returning fallback cache data for {endpoint_name} due to scraping failure")
            return cached_response['data'], cached_response['cached']
        
        # No cache available, return error
        logger.error(f"No cached data available for {endpoint_name}")
        return None, False
    
    except Exception as e:
        logger.error(f"Unexpected error in get_content_with_cache: {e}")
        return None, False


def parse_html_content(html_content):
    """
    Parse HTML content and extract structured data.
    
    Args:
        html_content (str): Raw HTML content
        
    Returns:
        dict: Parsed data from HTML tables
    """
    if not html_content:
        return {"data": {"header": [], "body": [], "footer": []}, "message": "No content to parse."}
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Find the specific table by class 'tb_base tb_dados'
    table_tag = soup.find('table', class_='tb_base tb_dados')
    
    parsed_table_data = {"header": [], "body": [], "footer": []}

    if not table_tag:
        logger.info("No table with class 'tb_base tb_dados' found")
        return {"data": parsed_table_data, "message": "Table not found or empty."}

    # Parse header
    thead_tag = table_tag.find('thead')
    parsed_table_data["header"] = _parse_html_table_section(thead_tag)

    # Parse footer
    tfoot_tag = table_tag.find('tfoot')
    parsed_table_data["footer"] = _parse_html_table_section(tfoot_tag)

    # Parse body
    tbody_tag = table_tag.find('tbody')
    if tbody_tag:
        parsed_table_data["body"] = _parse_tbody_with_grouped_items(tbody_tag)
    else:
        # Fallback for tables without an explicit <tbody>
        logger.info("No explicit tbody found in table. Using fallback parsing for body.")
        parsed_table_data["body"] = _parse_table_rows_fallback(table_tag, thead_tag, tfoot_tag)
        
    return {"data": parsed_table_data}


def get_content(url):
    """
    Legacy function for backward compatibility.
    Fetches content from a URL, parses an HTML table, and returns its data.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        parsed_data = parse_html_content(response.text)
        return jsonify(parsed_data)

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for URL {url}: {e}")
        return jsonify({"error": f"Request failed: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing content from {url}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while parsing the table content."}), 500

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask app on {host}:{port}")
    logger.info(f"Redis connection: {'available' if cache_manager.redis_client else 'unavailable'}")
    
    app.run(host=host, port=port, debug=debug)
