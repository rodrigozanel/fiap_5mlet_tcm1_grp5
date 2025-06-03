#!/usr/bin/env python3
"""
Script para testar endpoints da aplicação Flask no Elastic Beanstalk
"""

import requests
import time
from requests.auth import HTTPBasicAuth

# Configurações
BASE_URL = "http://flask-vitivinicola-api-env.eba-h8ms2mq2.us-east-2.elasticbeanstalk.com"
BASIC_AUTH = HTTPBasicAuth('user1', 'password1')
TIMEOUT = 10

def test_endpoint(url, description, auth=None, expected_status=200):
    """Test a specific endpoint"""
    print(f"\n🔍 Testando: {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, auth=auth, timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == expected_status:
            print(f"✅ SUCCESS: {description}")
            if len(response.text) < 500:
                print(f"Response: {response.text}")
            else:
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"❌ FAILED: Expected {expected_status}, got {response.status_code}")
            print(f"Response: {response.text}")
            
        return response.status_code == expected_status
        
    except requests.exceptions.Timeout:
        print(f"⏰ TIMEOUT: Request took longer than {TIMEOUT} seconds")
        return False
    except requests.exceptions.ConnectionError:
        print(f"🚫 CONNECTION ERROR: Cannot connect to server")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        return False

def main():
    print("🚀 Flask Vitivinícola API - Endpoint Testing")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health Check (sem auth)
    results.append(test_endpoint(
        f"{BASE_URL}/heartbeat",
        "Health Check (sem autenticação)"
    ))
    
    # Test 2: Root endpoint
    results.append(test_endpoint(
        BASE_URL,
        "Root endpoint",
        expected_status=401  # Expecting auth required
    ))
    
    # Test 3: Swagger Docs (sem auth)
    results.append(test_endpoint(
        f"{BASE_URL}/apidocs/",
        "Swagger Documentation (sem autenticação)"
    ))
    
    # Test 4: API with auth
    results.append(test_endpoint(
        f"{BASE_URL}/producao?year=2023",
        "API Produção (com autenticação)",
        auth=BASIC_AUTH
    ))
    
    # Test 5: Wrong URL (common mistake)
    results.append(test_endpoint(
        f"{BASE_URL}//heartbeat",  # Double slash
        "URL com barra dupla (erro comum)",
        expected_status=404
    ))
    
    # Summary
    print(f"\n📊 RESUMO DOS TESTES")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"✅ Sucessos: {passed}/{total}")
    print(f"❌ Falhas: {total - passed}/{total}")
    
    if passed == 0:
        print(f"\n🚨 PROBLEMA CRÍTICO: Nenhum endpoint respondeu")
        print("Possíveis causas:")
        print("- Load Balancer não roteando para containers")
        print("- Containers não estão rodando")
        print("- Health check falhando")
        print("- Problema de configuração de rede")
        
    elif passed < total:
        print(f"\n⚠️  PROBLEMA PARCIAL: Alguns endpoints falharam")
        print("Verifique configuração de autenticação e rotas")
        
    else:
        print(f"\n🎉 SUCESSO: Todos os testes passaram!")
        print("Aplicação está funcionando corretamente")

if __name__ == "__main__":
    main() 