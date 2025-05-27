import urllib.parse
import requests
from bs4 import BeautifulSoup
from flask import jsonify

# Mapping between route names and their corresponding 'opcao' values
ROUTE_OPCAO_MAP = {
    'producao': 'opt_02',
    'processamento': 'opt_03',
    'comercializacao': 'opt_04',
    'importacao': 'opt_05',
    'exportacao': 'opt_06'
}

# Validation constants
VALID_YEARS = list(range(1970, 2025))  # 1970-2024
VALID_SUB_OPTIONS = {
    'producao': ['VINHO DE MESA', 'VINHO FINO DE MESA (VINIFERA)', 'SUCO DE UVA', 'DERIVADOS'],
    'processamento': ['viniferas', 'americanas', 'mesa', 'semclass'],
    'comercializacao': ['VINHO DE MESA', 'ESPUMANTES', 'UVAS FRESCAS', 'SUCO DE UVA'],
    'importacao': ['vinhos', 'espumantes', 'frescas', 'passas', 'suco'],
    'exportacao': ['vinho', 'uva', 'espumantes', 'suco']
}

baseURL = "http://vitibrasil.cnpuv.embrapa.br/index.php"

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

# Helper functions for parsing table data - MOVED FROM APP.PY
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

def parse_html_content(html_content, logger):
    """
    Parse HTML content and extract structured data.
    
    Args:
        html_content (str): Raw HTML content
        logger: Logger instance for logging messages
        
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

def get_content_with_cache(endpoint_name, url, cache_manager, logger, params=None):
    """
    Fetch content with two-layer caching strategy.
    
    Args:
        endpoint_name (str): Name of the endpoint for cache key generation
        url (str): The URL to fetch content from
        cache_manager: CacheManager instance
        logger: Logger instance for logging messages
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
        parsed_data = parse_html_content(response.text, logger)
        
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

def get_content(url, logger):
    """
    Legacy function for backward compatibility.
    Fetches content from a URL, parses an HTML table, and returns its data.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        parsed_data = parse_html_content(response.text, logger)
        return jsonify(parsed_data)

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for URL {url}: {e}")
        return jsonify({"error": f"Request failed: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing content from {url}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while parsing the table content."}), 500 