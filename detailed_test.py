#!/usr/bin/env python3
"""
Teste detalhado da API Flask de Web Scraping
"""

import requests
from requests.auth import HTTPBasicAuth
import json

def detailed_test():
    """Teste detalhado dos endpoints da API"""
    
    # Configuração
    base_url = "http://localhost:5000"
    auth = HTTPBasicAuth('user1', 'password1')
    
    print("🔍 Teste Detalhado da API Flask de Web Scraping")
    print("=" * 60)
    
    # Teste 1: Endpoint de produção sem filtros
    print("\n📊 Teste 1: Dados de Produção (sem filtros)")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/producao", auth=auth, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            
            if 'data' in data:
                table_data = data['data']
                
                # Analisar header
                if table_data.get('header'):
                    print(f"📋 Header: {len(table_data['header'])} linha(s)")
                    for i, header_row in enumerate(table_data['header']):
                        print(f"   Linha {i+1}: {header_row}")
                
                # Analisar body
                if table_data.get('body'):
                    print(f"📄 Body: {len(table_data['body'])} item(s)")
                    for i, body_item in enumerate(table_data['body'][:3]):  # Mostrar apenas os 3 primeiros
                        if isinstance(body_item, dict):
                            print(f"   Item {i+1}:")
                            print(f"     - Dados principais: {body_item.get('item_data', [])}")
                            print(f"     - Sub-itens: {len(body_item.get('sub_items', []))}")
                        else:
                            print(f"   Item {i+1}: {body_item}")
                
                # Analisar footer
                if table_data.get('footer'):
                    print(f"🔻 Footer: {len(table_data['footer'])} linha(s)")
                    for i, footer_row in enumerate(table_data['footer']):
                        print(f"   Linha {i+1}: {footer_row}")
            
        else:
            print(f"❌ Erro: Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    # Teste 2: Endpoint com filtro de ano
    print("\n📊 Teste 2: Dados de Produção (com filtro de ano)")
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
            print(f"✅ Status: {response.status_code}")
            print(f"🔍 Parâmetros: year=2023")
            
            if 'data' in data:
                table_data = data['data']
                print(f"📋 Header: {len(table_data.get('header', []))} linha(s)")
                print(f"📄 Body: {len(table_data.get('body', []))} item(s)")
                print(f"🔻 Footer: {len(table_data.get('footer', []))} linha(s)")
            
        else:
            print(f"❌ Erro: Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    # Teste 3: Verificar autenticação
    print("\n🔐 Teste 3: Verificação de Autenticação")
    print("-" * 40)
    
    try:
        # Teste sem autenticação
        response = requests.get(f"{base_url}/producao", timeout=10)
        print(f"Sem auth: Status {response.status_code} (esperado: 401)")
        
        # Teste com credenciais inválidas
        wrong_auth = HTTPBasicAuth('wrong', 'credentials')
        response = requests.get(f"{base_url}/producao", auth=wrong_auth, timeout=10)
        print(f"Auth inválida: Status {response.status_code} (esperado: 401)")
        
        # Teste com credenciais válidas
        response = requests.get(f"{base_url}/producao", auth=auth, timeout=10)
        print(f"Auth válida: Status {response.status_code} (esperado: 200)")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    # Teste 4: Verificar todos os endpoints rapidamente
    print("\n🚀 Teste 4: Verificação Rápida de Todos os Endpoints")
    print("-" * 40)
    
    endpoints = ['/producao', '/processamento', '/comercializacao', '/importacao', '/exportacao']
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", auth=auth, timeout=15)
            status_icon = "✅" if response.status_code == 200 else "❌"
            print(f"{status_icon} {endpoint}: {response.status_code}")
            
        except Exception as e:
            print(f"❌ {endpoint}: Erro - {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 Teste detalhado concluído!")
    print("\n💡 Dicas:")
    print("   - Acesse a documentação Swagger: http://localhost:5000/apidocs/")
    print("   - Use os parâmetros 'year' e 'sub_option' para filtrar dados")
    print("   - Credenciais: user1/password1 ou user2/password2")

if __name__ == "__main__":
    detailed_test() 