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
    'description': f'''API para extração de dados vitivinícolas do site da Embrapa via web scraping com sistema avançado de cache três camadas

## Sistema de Cache Três Camadas

### 🚀 Camada 1: Cache Curto Prazo (Redis) - 5 minutos
Para respostas rápidas em requisições frequentes

### 🛡️ Camada 2: Cache Fallback (Redis) - 30 dias  
Backup para quando web scraping falha

### 📁 Camada 3: Fallback CSV (Arquivos Locais)
Última linha de defesa com dados estáticos

## Estados de Cache na Resposta
- `"cached": false` - Dados frescos via web scraping
- `"cached": "short_term"` - Cache Redis de 5 minutos  
- `"cached": "fallback"` - Cache Redis de 30 dias
- `"cached": "csv_fallback"` - Dados estáticos de arquivos CSV locais

## Garantia de Disponibilidade
A API **sempre responde** mesmo quando:
- ❌ Site da Embrapa indisponível
- ❌ Redis indisponível  
- ❌ Falhas de rede
- ✅ Fallback automático para CSV local

Versão: {VERSION_INFO["version"]}
Ambiente: {VERSION_INFO["environment"]}
Data: {VERSION_INFO["build_date"]}''',
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
    API health check endpoint.
    ---
    responses:
      200:
        description: API is running and healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: "healthy"
            timestamp:
              type: string
              example: "2023-01-01T00:00:00Z"
            redis:
              type: string
              example: "connected"
            csv_fallback:
              type: string
              example: "available"
    """
    try:
        # Check Redis connection safely
        redis_status = "disconnected"
        try:
            if cache_manager.redis_client:
                cache_manager.redis_client.ping()
                redis_status = "connected"
        except Exception:
            redis_status = "disconnected"
        
        # Check CSV fallback
        csv_status = "available" if cache_manager.csv_fallback else "unavailable"
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "redis": redis_status,
            "csv_fallback": csv_status
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@app.route("/producao", methods=["GET"])
@auth.login_required
def producao():
    """
    Busca dados de produção com sistema de cache três camadas.
    ---
    parameters:
      - name: year
        in: query
        type: integer
        minimum: 1970
        maximum: 2024
        required: true
        description: O ano para filtrar os dados (1970-2024). Campo obrigatório.
      - name: sub_option
        in: query
        type: string
        required: false
        enum: ["VINHO DE MESA", "VINHO FINO DE MESA (VINIFERA)", "SUCO DE UVA", "DERIVADOS"]
        description: A sub-opção para filtrar os dados de produção.
    responses:
      200:
        description: Dados de produção recuperados com sucesso através do sistema de cache três camadas.
        schema:
          type: object
          properties:
            data:
              type: object
              properties:
                header:
                  type: array
                  items:
                    type: array
                    items:
                      type: string
                  description: Cabeçalhos da tabela
                body:
                  type: array
                  items:
                    type: object
                    properties:
                      item_data:
                        type: array
                        items:
                          type: string
                      sub_items:
                        type: array
                        items:
                          type: array
                          items:
                            type: string
                  description: Dados principais da tabela
                footer:
                  type: array
                  items:
                    type: array
                    items:
                      type: string
                  description: Rodapé da tabela (totais)
            cached:
              type: string
              enum: [false, "short_term", "fallback", "csv_fallback"]
              description: Estado do cache usado para obter os dados
            year:
              type: string
              description: Ano dos dados retornados (extraído automaticamente ou do parâmetro)
              example: "2024"
            cache_info:
              type: object
              properties:
                active_cache_layer:
                  type: string
                  description: Camada de cache ativa utilizada
                  example: "short_term"
                layer_description:
                  type: string
                  description: Descrição da camada de cache utilizada
                  example: "Fast cache (5 minutes)"
                ttl_seconds:
                  type: object
                  properties:
                    short_cache:
                      type: [integer, string, "null"]
                      description: TTL em segundos do cache curto prazo (null se não existir)
                      example: 245
                    fallback_cache:
                      type: [integer, string, "null"]
                      description: TTL em segundos do cache fallback (null se não existir)
                      example: 2547891
                    csv_fallback:
                      type: string
                      description: TTL do fallback CSV (sempre 'indefinite')
                      example: "indefinite"
              description: Informações detalhadas sobre TTL das camadas de cache
            cache_expires_in:
              type: string
              description: Tempo até expiração do cache em formato humano
              example: "4m 5s"
            data_source:
              type: string
              description: Fonte dos dados retornados
              example: "Redis short_term cache"
            freshness:
              type: string
              description: Nível de atualização dos dados
              example: "Cached data"
            endpoint:
              type: string
              description: Nome do endpoint
              example: "producao"
            status:
              type: string
              description: Status da operação
              example: "success"
            metadata:
              type: object
              description: Metadados técnicos detalhados (informações internas)
      400:
        description: Parâmetros inválidos (ano fora do range ou sub-opção inválida).
        schema:
          type: object
          properties:
            error:
              type: string
              description: Mensagem de erro
            provided_params:
              type: object
              description: Parâmetros fornecidos
            status:
              type: string
              example: "parameter_error"
      503:
        description: Dados temporariamente indisponíveis (todas as camadas de cache falharam).
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Data temporarily unavailable"
            troubleshooting:
              type: object
              description: Sugestões para resolução do problema
            system_status:
              type: object
              description: Status das camadas de cache
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
        required: true
        description: O ano para filtrar os dados (1970-2024). Campo obrigatório.
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
    Busca dados de comercialização com sistema de cache três camadas.
    ---
    parameters:
      - name: year
        in: query
        type: integer
        minimum: 1970
        maximum: 2024
        required: true
        description: O ano para filtrar os dados (1970-2024). Campo obrigatório.
      - name: sub_option
        in: query
        type: string
        required: false
        enum: ["VINHO DE MESA", "ESPUMANTES", "UVAS FRESCAS", "SUCO DE UVA"]
        description: A sub-opção para filtrar os dados de comercialização.
    responses:
      200:
        description: Dados de comercialização recuperados com sucesso através do sistema de cache três camadas.
        schema:
          type: object
          properties:
            data:
              type: object
              description: Dados estruturados extraídos das tabelas
            cached:
              type: string
              enum: [false, "short_term", "fallback", "csv_fallback"]
              description: Fonte dos dados (fresh/cache Redis/CSV local)
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
      503:
        description: Serviço indisponível - todas as camadas de cache falharam.
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
        required: true
        description: O ano para filtrar os dados (1970-2024). Campo obrigatório.
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
        required: true
        description: O ano para filtrar os dados (1970-2024). Campo obrigatório.
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
