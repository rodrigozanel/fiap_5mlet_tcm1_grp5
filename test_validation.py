#!/usr/bin/env python3
"""
Teste de validação de parâmetros para a API Flask de Web Scraping
Testa as novas validações implementadas para year e sub_option
"""

import requests
from requests.auth import HTTPBasicAuth
import json

def test_parameter_validation():
    """Testa as validações de parâmetros year e sub_option"""
    
    # Configuração
    base_url = "http://localhost:5000"
    auth = HTTPBasicAuth('user1', 'password1')
    
    print("🔍 Teste de Validação de Parâmetros")
    print("=" * 60)
    
    # Definir sub-opções válidas para cada endpoint
    valid_sub_options = {
        'producao': ['VINHO DE MESA', 'VINHO FINO DE MESA (VINIFERA)', 'SUCO DE UVA', 'DERIVADOS'],
        'processamento': ['viniferas', 'americanas', 'mesa', 'semclass'],
        'comercializacao': ['VINHO DE MESA', 'ESPUMANTES', 'UVAS FRESCAS', 'SUCO DE UVA'],
        'importacao': ['vinhos', 'espumantes', 'frescas', 'passas', 'suco'],
        'exportacao': ['vinho', 'uva', 'espumantes', 'suco']
    }
    
    # Teste 1: Validação de anos válidos
    print("\n📅 Teste 1: Validação de Anos")
    print("-" * 40)
    
    test_years = [
        ('1970', True, 'Ano mínimo válido'),
        ('2024', True, 'Ano máximo válido'),
        ('2000', True, 'Ano válido no meio do range'),
        ('1969', False, 'Ano abaixo do mínimo'),
        ('2025', False, 'Ano acima do máximo'),
        ('abc', False, 'Ano não numérico'),
        ('', False, 'Ano vazio (agora obrigatório)')
    ]
    
    for year, should_pass, description in test_years:
        try:
            params = {'year': year} if year else {}
            response = requests.get(f"{base_url}/producao", auth=auth, params=params, timeout=10)
            
            if should_pass:
                if response.status_code == 200:
                    print(f"✅ {description}: PASSOU (Status: {response.status_code})")
                else:
                    print(f"❌ {description}: FALHOU - Esperado 200, recebido {response.status_code}")
                    if response.status_code == 400:
                        error_data = response.json()
                        print(f"   Erro: {error_data.get('error', 'N/A')}")
            else:
                if response.status_code == 400:
                    error_data = response.json()
                    print(f"✅ {description}: PASSOU (Status: {response.status_code})")
                    print(f"   Erro esperado: {error_data.get('error', 'N/A')}")
                else:
                    print(f"❌ {description}: FALHOU - Esperado 400, recebido {response.status_code}")
                    
        except Exception as e:
            print(f"❌ {description}: ERRO - {str(e)}")
    
    # Teste 2: Validação de sub-opções por endpoint
    print("\n🎯 Teste 2: Validação de Sub-opções por Endpoint")
    print("-" * 40)
    
    for endpoint, valid_options in valid_sub_options.items():
        print(f"\n📊 Testando /{endpoint}:")
        
        # Testar opção válida
        if valid_options:
            valid_option = valid_options[0]
            try:
                response = requests.get(
                    f"{base_url}/{endpoint}", 
                    auth=auth, 
                    params={'year': '2023', 'sub_option': valid_option}, 
                    timeout=15
                )
                
                if response.status_code == 200:
                    print(f"  ✅ Opção válida '{valid_option}': PASSOU")
                else:
                    print(f"  ❌ Opção válida '{valid_option}': FALHOU (Status: {response.status_code})")
                    
            except Exception as e:
                print(f"  ❌ Opção válida '{valid_option}': ERRO - {str(e)}")
        
        # Testar opção inválida
        invalid_option = 'OPCAO_INEXISTENTE'
        try:
            response = requests.get(
                f"{base_url}/{endpoint}", 
                auth=auth, 
                params={'year': '2023', 'sub_option': invalid_option}, 
                timeout=10
            )
            
            if response.status_code == 400:
                error_data = response.json()
                print(f"  ✅ Opção inválida '{invalid_option}': PASSOU (rejeitada corretamente)")
                print(f"     Erro: {error_data.get('error', 'N/A')}")
            else:
                print(f"  ❌ Opção inválida '{invalid_option}': FALHOU - Esperado 400, recebido {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Opção inválida '{invalid_option}': ERRO - {str(e)}")
    
    # Teste 3: Combinações de parâmetros
    print("\n🔄 Teste 3: Combinações de Parâmetros")
    print("-" * 40)
    
    test_combinations = [
        ({'year': '2023', 'sub_option': 'VINHO DE MESA'}, 'producao', True, 'Ambos válidos'),
        ({'year': '1969', 'sub_option': 'VINHO DE MESA'}, 'producao', False, 'Ano inválido, sub-opção válida'),
        ({'year': '2023', 'sub_option': 'OPCAO_INEXISTENTE'}, 'producao', False, 'Ano válido, sub-opção inválida'),
        ({'year': '1969', 'sub_option': 'OPCAO_INEXISTENTE'}, 'producao', False, 'Ambos inválidos'),
        ({}, 'producao', False, 'Sem parâmetros (ano agora obrigatório)')
    ]
    
    for params, endpoint, should_pass, description in test_combinations:
        try:
            response = requests.get(f"{base_url}/{endpoint}", auth=auth, params=params, timeout=10)
            
            if should_pass:
                if response.status_code == 200:
                    print(f"✅ {description}: PASSOU")
                else:
                    print(f"❌ {description}: FALHOU - Esperado 200, recebido {response.status_code}")
            else:
                if response.status_code == 400:
                    error_data = response.json()
                    print(f"✅ {description}: PASSOU (rejeitado corretamente)")
                    print(f"   Erro: {error_data.get('error', 'N/A')}")
                else:
                    print(f"❌ {description}: FALHOU - Esperado 400, recebido {response.status_code}")
                    
        except Exception as e:
            print(f"❌ {description}: ERRO - {str(e)}")
    
    # Teste 4: Verificar estrutura de resposta de erro
    print("\n📋 Teste 4: Estrutura de Resposta de Erro")
    print("-" * 40)
    
    try:
        response = requests.get(
            f"{base_url}/producao", 
            auth=auth, 
            params={'year': '1969'}, 
            timeout=10
        )
        
        if response.status_code == 400:
            error_data = response.json()
            print("✅ Resposta de erro 400 recebida")
            
            # Verificar estrutura
            if 'error' in error_data:
                print("✅ Campo 'error' presente na resposta")
                print(f"   Mensagem: {error_data['error']}")
            else:
                print("❌ Campo 'error' ausente na resposta")
                
            # Verificar se é JSON válido
            print("✅ Resposta é JSON válido")
            
        else:
            print(f"❌ Esperado status 400, recebido {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao testar estrutura de resposta: {str(e)}")
    
    # Teste 5: Performance com validação
    print("\n⚡ Teste 5: Performance com Validação")
    print("-" * 40)
    
    import time
    
    try:
        start_time = time.time()
        response = requests.get(
            f"{base_url}/producao", 
            auth=auth, 
            params={'year': '2023', 'sub_option': 'VINHO DE MESA'}, 
            timeout=30
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            print(f"✅ Requisição válida processada em {response_time:.3f}s")
            
            # Verificar se há flag de cache
            data = response.json()
            cached_flag = data.get('cached', False)
            print(f"✅ Cache status: {cached_flag}")
            
        else:
            print(f"❌ Erro na requisição: Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro no teste de performance: {str(e)}")
    
    # Teste 6: Verificar que ano é obrigatório para todos os endpoints
    print("\n📋 Teste 6: Verificação de Campo Ano Obrigatório")
    print("-" * 40)
    
    endpoints = ['producao', 'processamento', 'comercializacao', 'importacao', 'exportacao']
    
    for endpoint in endpoints:
        try:
            # Testar sem parâmetro year
            response = requests.get(f"{base_url}/{endpoint}", auth=auth, timeout=10)
            
            if response.status_code == 400:
                error_data = response.json()
                if 'obrigatório' in error_data.get('error', '').lower():
                    print(f"✅ /{endpoint}: Campo ano verificado como obrigatório")
                    print(f"   Erro: {error_data.get('error', 'N/A')}")
                else:
                    print(f"❌ /{endpoint}: Erro 400 mas não por ano obrigatório")
            else:
                print(f"❌ /{endpoint}: Esperado 400 por ano obrigatório, recebido {response.status_code}")
                
        except Exception as e:
            print(f"❌ /{endpoint}: ERRO - {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 Teste de Validação Concluído!")
    print("\n📊 Resumo dos Testes:")
    print("   ✅ Validação de anos (1970-2024)")
    print("   ✅ Validação de sub-opções por endpoint")
    print("   ✅ Combinações de parâmetros")
    print("   ✅ Estrutura de resposta de erro")
    print("   ✅ Performance com validação")
    print("   ✅ Verificação de campo ano obrigatório")
    print("\n💡 Próximos passos:")
    print("   - Execute os outros testes: python test_api.py")
    print("   - Verifique a documentação Swagger: http://localhost:5000/apidocs/")

if __name__ == "__main__":
    test_parameter_validation() 