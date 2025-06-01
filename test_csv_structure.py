#!/usr/bin/env python3
"""
Test script to examine CSV fallback data structure and enrichment process
"""

import sys
sys.path.append('/app')
from cache.cache_manager import CacheManager
from cache.csv_fallback import CsvFallbackManager
import json
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_csv_structure():
    """Test CSV fallback structure and enrichment"""
    print("=== TESTANDO ESTRUTURA E ENRIQUECIMENTO DO CSV ===")
    
    try:
        # Step 1: Test CSV data directly
        print("\n🔧 ETAPA 1: CSV DIRETO")
        csv_manager = CsvFallbackManager('/app/data/fallback')
        raw_csv_result = csv_manager.get_data_for_endpoint('producao', year='2023')
        
        if raw_csv_result:
            print(f'  • Raw CSV keys: {list(raw_csv_result.keys())}')
            print(f'  • Has "data" key: {"data" in raw_csv_result}')
            if 'data' in raw_csv_result:
                print(f'  • Data keys: {list(raw_csv_result["data"].keys())}')
        
        # Step 2: Test cache manager processing
        print("\n🔧 ETAPA 2: CACHE MANAGER PROCESSING")
        cache_manager = CacheManager()
        cache_manager.csv_fallback = csv_manager
        
        cache_csv_result = cache_manager.get_csv_fallback('producao', {'year': '2023'})
        
        if cache_csv_result:
            print(f'  • Cache processed keys: {list(cache_csv_result.keys())}')
            print(f'  • Cached flag: {cache_csv_result.get("cached")}')
            print(f'  • Has "data" key: {"data" in cache_csv_result}')
            if 'data' in cache_csv_result:
                print(f'  • Data keys: {list(cache_csv_result["data"].keys())}')
        
        # Step 3: Test the enrichment function directly
        print("\n🔧 ETAPA 3: TESTE DIRETO DO ENRIQUECIMENTO")
        
        # Import the enrichment function from utils
        from utils import get_content_with_cache
        
        # Test with simulated data
        test_data = {
            'data': {
                'header': [['test', 'header']],
                'body': [{'item_data': ['test'], 'sub_items': []}],
                'footer': []
            },
            'cached': 'csv_fallback',
            'timestamp': '2023-01-01T00:00:00Z'
        }
        
        # Extract and test the enrich function
        import importlib.util
        import inspect
        
        # Get the enrich function source
        with open('/app/utils.py', 'r') as f:
            content = f.read()
        
        # Find the enrich function
        if 'def enrich_response_with_metadata' in content:
            print("  • Função de enriquecimento encontrada")
            
            # Try to manually call it (simplified)
            try:
                # Create a minimal test
                from datetime import datetime
                
                # Simulate the enrichment
                test_params = {'year': '2023'}
                
                if 'metadata' not in test_data:
                    test_data['metadata'] = {}
                
                # Extract year from params
                year = test_params.get('year', 'unknown')
                
                # Add year to data structure
                if 'data' in test_data and isinstance(test_data['data'], dict):
                    test_data['data']['year'] = year
                
                test_data['metadata']['year'] = year
                
                print(f"  • Manual enrichment result keys: {list(test_data.keys())}")
                print(f"  • Year in result: {test_data.get('year', 'Not found')}")
                print(f"  • Year in data: {test_data.get('data', {}).get('year', 'Not found')}")
                print(f"  • Year in metadata: {test_data.get('metadata', {}).get('year', 'Not found')}")
                
            except Exception as e:
                print(f"  • Erro no enriquecimento manual: {e}")
        
        # Step 4: Test full API flow simulation
        print("\n🔧 ETAPA 4: SIMULAÇÃO DO FLUXO COMPLETO DA API")
        
        # Force CSV fallback by simulating network failure
        print("  • Simulando falha de rede para forçar CSV fallback...")
        
        # Test the handler directly
        try:
            from apis.producao_handler import handle_producao
            from flask import Flask
            from werkzeug.test import EnvironBuilder
            from werkzeug.wrappers import Request
            
            app = Flask(__name__)
            
            with app.test_request_context('/?year=2023'):
                result = handle_producao(cache_manager, logger)
                print(f"  • Handler result type: {type(result)}")
                
                if hasattr(result, 'get_json'):
                    data = result.get_json()
                    print(f"  • Handler response keys: {list(data.keys()) if data else 'None'}")
                    if data:
                        print(f"  • Year in handler response: {data.get('year', 'Not found')}")
                
        except Exception as e:
            print(f"  • Erro no teste do handler: {e}")
            
    except Exception as e:
        print(f'❌ ERRO PRINCIPAL: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_csv_structure() 