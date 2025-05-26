import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from flasgger import Swagger
import urllib.parse

app = Flask(__name__)

app.config['SWAGGER'] = {
    'title': 'Flask Web Scraping API - Dados Vitivinícolas Embrapa',
    'uiversion': 3,
    'description': 'API para extração de dados vitivinícolas do site da Embrapa via web scraping',
    'version': '1.0.0',
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
              example: "1.0.0"
            service:
              type: string
              example: "Flask Web Scraping API"
    """
    from datetime import datetime
    import time
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime": "API is running",
        "version": "1.0.0",
        "service": "Flask Web Scraping API - Dados Vitivinícolas Embrapa",
        "endpoints_available": 5,
        "authentication": "HTTP Basic Auth"
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
        type: string
        required: false
        description: O ano para filtrar os dados.
      - name: sub_option
        in: query
        type: string
        required: false
        description: A sub-opção para filtrar os dados.
    responses:
      200:
        description: Dados de produção recuperados com sucesso.
      401:
        description: Autenticação necessária.
    """
    route_name = request.endpoint
    year = request.args.get('year')
    sub_option = request.args.get('sub_option')
    url = build_url(route_name, year, sub_option)
    return get_content(url), 200


@app.route("/processamento", methods=["GET"])
@auth.login_required
def processamento():    
    """
    Busca dados de processamento.
    ---
    parameters:
      - name: year
        in: query
        type: string
        required: false
        description: O ano para filtrar os dados.
      - name: sub_option
        in: query
        type: string
        required: false
        description: A sub-opção para filtrar os dados.
    responses:
      200:
        description: Dados de processamento recuperados com sucesso.
      401:
        description: Autenticação necessária.
    """    
    route_name = request.endpoint
    year = request.args.get('year')
    sub_option = request.args.get('sub_option')
    url = build_url(route_name, year, sub_option)
    return get_content(url), 200


@app.route("/comercializacao", methods=["GET"])
@auth.login_required
def comercializacao():
    """
    Busca dados de comercialização.
    ---
    parameters:
      - name: year
        in: query
        type: string
        required: false
        description: O ano para filtrar os dados.
      - name: sub_option
        in: query
        type: string
        required: false
        description: A sub-opção para filtrar os dados.
    responses:
      200:
        description: Dados de comercialização recuperados com sucesso.
      401:
        description: Autenticação necessária.
    """
    route_name = request.endpoint
    year = request.args.get('year')
    sub_option = request.args.get('sub_option')
    url = build_url(route_name, year, sub_option)
    return get_content(url), 200


@app.route("/importacao", methods=["GET"])
@auth.login_required
def importacao():    
    """
    Busca dados de importação.
    ---
    parameters:
      - name: year
        in: query
        type: string
        required: false
        description: O ano para filtrar os dados.
      - name: sub_option
        in: query
        type: string
        required: false
        description: A sub-opção para filtrar os dados.
    responses:
      200:
        description: Dados de importação recuperados com sucesso.
      401:
        description: Autenticação necessária.
    """
    route_name = request.endpoint
    year = request.args.get('year')
    sub_option = request.args.get('sub_option')
    url = build_url(route_name, year, sub_option)
    return get_content(url), 200


@app.route("/exportacao", methods=["GET"])
@auth.login_required
def exportacao():
    """
    Busca dados de exportação.
    ---
    parameters:
      - name: year
        in: query
        type: string
        required: false
        description: O ano para filtrar os dados.
      - name: sub_option
        in: query
        type: string
        required: false
        description: A sub-opção para filtrar os dados.
    responses:
      200:
        description: Dados de exportação recuperados com sucesso.
      401:
        description: Autenticação necessária.
    """
    route_name = request.endpoint
    year = request.args.get('year')
    sub_option = request.args.get('sub_option')
    url = build_url(route_name, year, sub_option)
    return get_content(url), 200


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

def get_content(url):
    """
    Fetches content from a URL, parses an HTML table, and returns its data.
    Handles tables with thead, tbody, tfoot, and item/subitem structures in tbody.
    Includes fallback for tables without an explicit tbody.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the specific table by class 'tb_base tb_dados'
        table_tag = soup.find('table', class_='tb_base tb_dados')
        
        parsed_table_data = {"header": [], "body": [], "footer": []}

        if not table_tag:
            app.logger.info(f"No table with class 'tb_base tb_dados' found at {url}")
            return jsonify({"data": parsed_table_data, "message": "Table not found or empty."})

        # Parse header
        thead_tag = table_tag.find('thead')
        parsed_table_data["header"] = _parse_html_table_section(thead_tag) # Handles None thead_tag

        # Parse footer
        tfoot_tag = table_tag.find('tfoot')
        parsed_table_data["footer"] = _parse_html_table_section(tfoot_tag) # Handles None tfoot_tag

        # Parse body
        tbody_tag = table_tag.find('tbody')
        if tbody_tag:
            parsed_table_data["body"] = _parse_tbody_with_grouped_items(tbody_tag)
        else:
            # Fallback for tables without an explicit <tbody>
            app.logger.info(f"No explicit tbody found in table at {url}. Using fallback parsing for body.")
            parsed_table_data["body"] = _parse_table_rows_fallback(table_tag, thead_tag, tfoot_tag)
            
        return jsonify({"data": parsed_table_data})

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request failed for URL {url}: {e}")
        return jsonify({"error": f"Request failed: {str(e)}"}), 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred while processing content from {url}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while parsing the table content."}), 500

if __name__ == "__main__":
    app.run(debug=True)
