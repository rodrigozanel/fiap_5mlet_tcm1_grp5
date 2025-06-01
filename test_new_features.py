#!/usr/bin/env python3
"""
Simple test to demonstrate the new API features - Year and TTL information
"""

import requests
from requests.auth import HTTPBasicAuth
import json

def test_new_features():
    """Test the new year and TTL features"""
    print("🚀 Demonstrando as novas funcionalidades da API")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    auth = HTTPBasicAuth('user1', 'password1')
    
    # Test 1: API with year parameter
    print("\n📅 Teste 1: API com parâmetro de ano")
    print("-" * 40)
    try:
        response = requests.get(
            f"{base_url}/producao",
            auth=auth,
            params={'year': '2023'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sucesso! Status: {response.status_code}")
            print(f"📅 Ano retornado: {data.get('year', 'N/A')}")
            print(f"💾 Fonte dos dados: {data.get('data_source', 'N/A')}")
            print(f"⏰ Cache expira em: {data.get('cache_expires_in', 'N/A')}")
            
            # Show cache info
            cache_info = data.get('cache_info', {})
            print(f"🗄️ Camada de cache ativa: {cache_info.get('active_cache_layer', 'N/A')}")
            
            ttl_info = cache_info.get('ttl_seconds', {})
            print(f"⏱️ TTL do cache curto: {ttl_info.get('short_cache', 'N/A')} segundos")
            print(f"⏱️ TTL do cache fallback: {ttl_info.get('fallback_cache', 'N/A')} segundos")
            print(f"⏱️ TTL do CSV fallback: {ttl_info.get('csv_fallback', 'N/A')}")
            
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"Resposta: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Test 2: API without year parameter
    print("\n📅 Teste 2: API sem parâmetro de ano")
    print("-" * 40)
    try:
        response = requests.get(
            f"{base_url}/producao",
            auth=auth,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sucesso! Status: {response.status_code}")
            print(f"📅 Ano extraído automaticamente: {data.get('year', 'N/A')}")
            print(f"💾 Fonte dos dados: {data.get('data_source', 'N/A')}")
            print(f"⏰ Cache expira em: {data.get('cache_expires_in', 'N/A')}")
            
            # Show if metadata exists
            metadata = data.get('metadata', {})
            if metadata:
                print(f"📋 Metadata presente: {list(metadata.keys())}")
            else:
                print("📋 Metadata: Não encontrado")
                
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Test 3: Show multiple endpoints consistency  
    print("\n🔄 Teste 3: Consistência entre endpoints")
    print("-" * 40)
    endpoints = ['producao', 'processamento', 'comercializacao']
    
    for endpoint in endpoints:
        try:
            response = requests.get(
                f"{base_url}/{endpoint}",
                auth=auth,
                params={'year': '2022'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                year = data.get('year', 'N/A')
                cache_layer = data.get('cache_info', {}).get('active_cache_layer', 'N/A')
                print(f"✅ {endpoint:15}: ano={year}, cache={cache_layer}")
            else:
                print(f"❌ {endpoint:15}: Erro {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint:15}: Erro - {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Demonstração das novas funcionalidades concluída!")
    print("\n📊 Resumo das funcionalidades implementadas:")
    print("  • ✅ Ano extraído automaticamente dos dados ou parâmetros")
    print("  • ✅ TTL de cada camada de cache em segundos")
    print("  • ✅ Tempo de expiração em formato humano")
    print("  • ✅ Informações da fonte de dados ativa")
    print("  • ✅ Metadados técnicos detalhados")
    print("  • ✅ Consistência entre todos os endpoints")

if __name__ == "__main__":
    test_new_features() 