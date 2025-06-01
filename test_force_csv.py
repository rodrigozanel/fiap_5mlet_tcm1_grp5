#!/usr/bin/env python3
"""
Test script to force CSV fallback and examine structure
"""

import sys
sys.path.append('/app')
import json
import logging
from unittest.mock import patch

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_force_csv_fallback():
    """Force CSV fallback and test structure"""
    print("=== TESTANDO CSV FALLBACK FORÇADO ===")
    
    try:
        # Import after setting path
        from cache.cache_manager import CacheManager
        from utils import get_content_with_cache, build_url
        from apis.producao_handler import handle_producao
        from flask import Flask
        
        # Initialize cache manager
        cache_manager = CacheManager()
        
        # Force Redis to be unavailable
        cache_manager.redis_client = None
        
        # Test parameters
        params = {'year': '2023'}
        endpoint_name = 'producao'
        
        print("\\n🔧 ETAPA 1: TESTANDO get_content_with_cache COM CSV FORÇADO")
        
        # Build URL (will be invalid due to our modification)
        url = build_url(endpoint_name, year='2023')
        print(f"URL gerada: {url}")
        
        # Call get_content_with_cache directly
        content, cached_flag = get_content_with_cache(endpoint_name, url, cache_manager, logger, params)
        
        if content:
            print(f"\\n✅ RESULTADO DO get_content_with_cache:")
            print(f"  • cached_flag: {cached_flag}")
            print(f"  • content keys: {list(content.keys())}")
            print(f"  • year no nível raiz: {content.get('year', 'Not found')}")
            print(f"  • year em data: {content.get('data', {}).get('year', 'Not found')}")
            print(f"  • cache_expires_in: {content.get('cache_expires_in', 'Not found')}")
            print(f"  • cache_info: {content.get('cache_info', 'Not found')}")
            print(f"  • endpoint: {content.get('endpoint', 'Not found')}")
            print(f"  • status: {content.get('status', 'Not found')}")
            print(f"  • metadata: {content.get('metadata', 'Not found')}")
        else:
            print("❌ Nenhum conteúdo retornado")
        
        print("\\n🔧 ETAPA 2: TESTANDO HANDLER COMPLETO")
        
        # Test with Flask context
        app = Flask(__name__)
        
        with app.test_request_context('/?year=2023'):
            # Patch the cache_manager in the handler
            with patch('apis.producao_handler.cache_manager', cache_manager):
                try:
                    result = handle_producao(cache_manager, logger)
                    print(f"  • Handler result type: {type(result)}")
                    
                    if isinstance(result, tuple) and len(result) >= 2:
                        response_obj, status_code = result
                        print(f"  • Status code: {status_code}")
                        
                        if hasattr(response_obj, 'get_json'):
                            data = response_obj.get_json()
                            if data:
                                print(f"\\n✅ ESTRUTURA DA RESPOSTA DO HANDLER:")
                                print(f"  • year no nível raiz: {data.get('year', 'Not found')}")
                                print(f"  • year em data: {data.get('data', {}).get('year', 'Not found')}")
                                print(f"  • cached: {data.get('cached', 'Not found')}")
                                print(f"  • cache_expires_in: {data.get('cache_expires_in', 'Not found')}")
                                print(f"  • cache_info: {data.get('cache_info', 'Not found')}")
                                print(f"  • endpoint: {data.get('endpoint', 'Not found')}")
                                print(f"  • status: {data.get('status', 'Not found')}")
                                print(f"  • data_source: {data.get('data_source', 'Not found')}")
                                print(f"  • freshness: {data.get('freshness', 'Not found')}")
                        
                except Exception as e:
                    print(f"  • Erro no handler: {e}")
                    import traceback
                    traceback.print_exc()
        
        print("\\n🔧 ETAPA 3: TESTE DIRETO DO CSV FALLBACK")
        
        # Test CSV fallback directly
        csv_result = cache_manager.get_csv_fallback(endpoint_name, params)
        if csv_result:
            print(f"\\n✅ RESULTADO DIRETO DO CSV FALLBACK:")
            print(f"  • Keys: {list(csv_result.keys())}")
            print(f"  • cached: {csv_result.get('cached')}")
            print(f"  • timestamp: {csv_result.get('timestamp')}")
            print(f"  • data keys: {list(csv_result.get('data', {}).keys())}")
            
            # Now test enrichment on this data
            from utils import get_content_with_cache
            
            # Get the enrichment function by calling get_content_with_cache but patching the CSV call
            print("\\n🔧 TESTANDO ENRIQUECIMENTO DIRETO NO CSV")
            
            # Manually call enrichment (simulate what happens in get_content_with_cache)
            # We need to extract the enrich function somehow
            import inspect
            import types
            
            # Get the source of get_content_with_cache
            source_lines = inspect.getsourcelines(get_content_with_cache)[0]
            
            # Find the enrich function definition
            enrich_start = None
            for i, line in enumerate(source_lines):
                if 'def enrich_response_with_metadata' in line:
                    enrich_start = i
                    break
            
            if enrich_start:
                print("  • Função de enriquecimento encontrada, simulando...")
                
                # Simulate enrichment manually
                enriched_csv = csv_result.copy()
                
                # Add year to metadata and data
                if 'metadata' not in enriched_csv:
                    enriched_csv['metadata'] = {}
                
                year = params.get('year', 'unknown')
                enriched_csv['metadata']['year'] = year
                
                if 'data' in enriched_csv and isinstance(enriched_csv['data'], dict):
                    enriched_csv['data']['year'] = year
                
                # Add TTL info (mock)
                enriched_csv['metadata']['cache_ttl'] = {
                    'short_cache_ttl': None,
                    'fallback_cache_ttl': None,
                    'csv_fallback_ttl': 'indefinite'
                }
                
                enriched_csv['metadata']['cache_status'] = {
                    'active_layer': 'csv_fallback',
                    'layer_description': 'Local file fallback'
                }
                
                print(f"\\n✅ CSV ENRIQUECIDO MANUALMENTE:")
                print(f"  • Keys após enriquecimento: {list(enriched_csv.keys())}")
                print(f"  • year no nível raiz: {enriched_csv.get('year', 'Not found')}")
                print(f"  • year em data: {enriched_csv.get('data', {}).get('year', 'Not found')}")
                print(f"  • year em metadata: {enriched_csv.get('metadata', {}).get('year', 'Not found')}")
                print(f"  • cache_status: {enriched_csv.get('metadata', {}).get('cache_status', 'Not found')}")
        
    except Exception as e:
        print(f'❌ ERRO PRINCIPAL: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_force_csv_fallback() 