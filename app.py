from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from flasgger import Swagger
import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import cache modules
from cache import CacheManager

# Import utilities
from utils import (
    build_url, validate_parameters, ROUTE_OPCAO_MAP, 
    VALID_YEARS, VALID_SUB_OPTIONS, baseURL,
    get_content_with_cache, parse_html_content, get_content,
    _parse_html_table_section, _parse_tbody_with_grouped_items, _parse_table_rows_fallback
)

# Import API Handlers
from apis.producao_handler import handle_producao
from apis.processamento_handler import handle_processamento
from apis.comercializacao_handler import handle_comercializacao
from apis.importacao_handler import handle_importacao
from apis.exportacao_handler import handle_exportacao

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

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username
    return None



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
def producao():
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
    return handle_producao(cache_manager, logger)


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
    return handle_processamento(cache_manager, logger)


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
    return handle_comercializacao(cache_manager, logger)


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
    return handle_importacao(cache_manager, logger)


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
    return handle_exportacao(cache_manager, logger)


if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask app on {host}:{port}")
    logger.info(f"Redis connection: {'available' if cache_manager.redis_client else 'unavailable'}")
    
    app.run(host=host, port=port, debug=debug)
