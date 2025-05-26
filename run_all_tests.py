#!/usr/bin/env python3
"""
Script para executar todos os testes da API Flask de Web Scraping
"""

import subprocess
import sys
import time
import requests

def check_api_running():
    """Verifica se a API está rodando"""
    try:
        response = requests.get("http://localhost:5000/heartbeat", timeout=5)
        return response.status_code == 200
    except:
        return False

def run_test_file(test_file, description):
    """Executa um arquivo de teste específico"""
    print(f"\n{'='*60}")
    print(f"🚀 Executando: {description}")
    print(f"📁 Arquivo: {test_file}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=False, 
                              text=True, 
                              timeout=120)
        
        if result.returncode == 0:
            print(f"\n✅ {description} - CONCLUÍDO COM SUCESSO")
        else:
            print(f"\n❌ {description} - FALHOU (código: {result.returncode})")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"\n⏰ {description} - TIMEOUT (mais de 2 minutos)")
        return False
    except Exception as e:
        print(f"\n❌ {description} - ERRO: {str(e)}")
        return False

def main():
    """Função principal que executa todos os testes"""
    
    print("🧪 SUITE COMPLETA DE TESTES - API Flask Web Scraping")
    print("=" * 60)
    print("📋 Esta suite executará todos os testes disponíveis:")
    print("   1. Teste de Heartbeat")
    print("   2. Teste de Validação de Parâmetros (NOVO)")
    print("   3. Teste Básico da API")
    print("   4. Teste Detalhado da API")
    print("=" * 60)
    
    # Verificar se a API está rodando
    print("\n🔍 Verificando se a API está rodando...")
    if not check_api_running():
        print("❌ API não está rodando em http://localhost:5000")
        print("💡 Para iniciar a API, execute: python app.py")
        print("💡 Ou com Docker: docker-compose up")
        return False
    
    print("✅ API está rodando e respondendo")
    
    # Lista de testes para executar
    tests = [
        ("test_heartbeat.py", "Teste de Heartbeat e Endpoints Básicos"),
        ("test_validation.py", "Teste de Validação de Parâmetros"),
        ("test_api.py", "Teste Básico da API"),
        ("detailed_test.py", "Teste Detalhado da API")
    ]
    
    results = []
    start_time = time.time()
    
    # Executar cada teste
    for test_file, description in tests:
        print(f"\n⏳ Aguardando 2 segundos antes do próximo teste...")
        time.sleep(2)
        
        success = run_test_file(test_file, description)
        results.append((description, success))
    
    # Resumo final
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n{'='*60}")
    print("📊 RESUMO FINAL DOS TESTES")
    print(f"{'='*60}")
    print(f"⏱️ Tempo total de execução: {total_time:.2f} segundos")
    print(f"📈 Testes executados: {len(results)}")
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    print(f"✅ Testes aprovados: {passed}")
    print(f"❌ Testes falharam: {failed}")
    
    print(f"\n📋 Detalhes por teste:")
    for description, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"   {status} - {description}")
    
    if failed == 0:
        print(f"\n🎉 TODOS OS TESTES PASSARAM! 🎉")
        print("✅ A API está funcionando corretamente com as novas validações")
    else:
        print(f"\n⚠️ {failed} teste(s) falharam. Verifique os logs acima.")
    
    print(f"\n💡 Próximos passos:")
    print("   - Acesse a documentação Swagger: http://localhost:5000/apidocs/")
    print("   - Teste manualmente os novos parâmetros de validação")
    print("   - Execute testes individuais se necessário")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 