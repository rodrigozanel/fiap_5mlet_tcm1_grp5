#!/usr/bin/env python3
"""
Teste específico para o endpoint de heartbeat da API Flask
"""

import requests
import json
from datetime import datetime

def test_heartbeat():
    """Testa o endpoint de heartbeat da API"""
    
    base_url = "http://localhost:5000"
    
    print("🔍 Teste do Endpoint de Heartbeat")
    print("=" * 40)
    
    try:
        # Teste do heartbeat
        print("\n💓 Testando /heartbeat...")
        response = requests.get(f"{base_url}/heartbeat", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Status da API: {data.get('status')}")
            print(f"✅ Timestamp: {data.get('timestamp')}")
            print(f"✅ Versão: {data.get('version')}")
            print(f"✅ Serviço: {data.get('service')}")
            print(f"✅ Endpoints disponíveis: {data.get('endpoints_available')}")
            print(f"✅ Tempo de resposta: {response.elapsed.total_seconds():.3f}s")
            
            # Verificar estrutura da resposta
            required_fields = ['status', 'timestamp', 'version', 'service']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print("✅ Todos os campos obrigatórios estão presentes")
            else:
                print(f"❌ Campos ausentes: {missing_fields}")
                
            # Verificar se o status é 'healthy'
            if data.get('status') == 'healthy':
                print("✅ API está saudável")
            else:
                print(f"⚠️ Status da API: {data.get('status')}")
                
        else:
            print(f"❌ Erro: Status {response.status_code}")
            print(f"❌ Resposta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        print("❌ Verifique se a aplicação está rodando em http://localhost:5000")
    except requests.exceptions.Timeout:
        print("❌ Erro: Timeout na requisição")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    
    # Teste dos endpoints de informação
    print("\n📋 Testando endpoints de informação...")
    
    endpoints_to_test = [
        ("/", "Página inicial"),
        ("/test", "Endpoint de teste")
    ]
    
    for endpoint, description in endpoints_to_test:
        try:
            print(f"\n🔗 Testando {endpoint} ({description})...")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"✅ Resposta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro ao testar {endpoint}: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 Teste de Heartbeat Concluído!")

if __name__ == "__main__":
    test_heartbeat() 