#!/usr/bin/env python3
"""
Script de teste para a API Flask de Web Scraping
"""

import requests
from requests.auth import HTTPBasicAuth
import json

def test_api():
    """Testa os endpoints da API"""
    
    # Configuração
    base_url = "http://localhost:5000"
    auth = HTTPBasicAuth('user1', 'password1')
    
    # Lista de endpoints para testar
    endpoints = [
        '/producao',
        '/processamento', 
        '/comercializacao',
        '/importacao',
        '/exportacao'
    ]
    
    print("🧪 Testando API Flask de Web Scraping")
    print("=" * 50)
    
    for endpoint in endpoints:
        try:
            print(f"\n📡 Testando {endpoint}...")
            
            # Fazer requisição
            response = requests.get(
                f"{base_url}{endpoint}",
                auth=auth,
                timeout=30
            )
            
            # Verificar status
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint}: OK")
                print(f"   Status: {response.status_code}")
                
                # Verificar estrutura básica da resposta
                if 'data' in data:
                    table_data = data['data']
                    print(f"   Header rows: {len(table_data.get('header', []))}")
                    print(f"   Body items: {len(table_data.get('body', []))}")
                    print(f"   Footer rows: {len(table_data.get('footer', []))}")
                else:
                    print(f"   Resposta: {data}")
                    
            else:
                print(f"❌ {endpoint}: ERRO")
                print(f"   Status: {response.status_code}")
                print(f"   Resposta: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: ERRO DE CONEXÃO")
            print(f"   Erro: {str(e)}")
        except Exception as e:
            print(f"❌ {endpoint}: ERRO INESPERADO")
            print(f"   Erro: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Teste concluído!")
    print("\n💡 Para acessar a documentação Swagger:")
    print(f"   {base_url}/apidocs/")

if __name__ == "__main__":
    test_api() 