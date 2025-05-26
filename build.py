#!/usr/bin/env python3
"""
Script de build que atualiza a versão automaticamente
Simula o processo de "compilação" para linguagens interpretadas
"""

import os
import sys
import subprocess
from version import version_manager

def run_command(command, description):
    """Executa um comando e exibe o resultado"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Sucesso")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erro: {e}")
        if e.stderr:
            print(f"   Erro: {e.stderr.strip()}")
        return False

def update_version():
    """Atualiza informações de versão"""
    print("🔄 Atualizando informações de versão...")
    version_info = version_manager.save_version_file()
    
    print(f"✅ Versão atualizada:")
    print(f"   Versão: {version_info['version']}")
    print(f"   Versão semântica: {version_info['semantic_version']}")
    print(f"   Build: {version_info['build_number']}")
    print(f"   Commit: {version_info['commit_hash']}")
    print(f"   Branch: {version_info['branch']}")
    
    return version_info

def run_tests():
    """Executa testes da aplicação"""
    print("\n🧪 Executando testes...")
    
    # Verifica se existem arquivos de teste
    test_files = [
        'test_api.py',
        'test_heartbeat.py', 
        'test_validation.py'
    ]
    
    available_tests = [f for f in test_files if os.path.exists(f)]
    
    if not available_tests:
        print("⚠️ Nenhum arquivo de teste encontrado")
        return True
    
    all_passed = True
    for test_file in available_tests:
        success = run_command(f"python {test_file}", f"Executando {test_file}")
        if not success:
            all_passed = False
    
    return all_passed

def validate_environment():
    """Valida o ambiente de desenvolvimento"""
    print("🔍 Validando ambiente...")
    
    # Verifica se está em um repositório Git
    if not os.path.exists('.git'):
        print("⚠️ Não é um repositório Git")
        return False
    
    # Verifica se há mudanças não commitadas
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print("⚠️ Há mudanças não commitadas:")
            print(result.stdout)
            return False
    except subprocess.CalledProcessError:
        print("❌ Erro ao verificar status do Git")
        return False
    
    print("✅ Ambiente validado")
    return True

def build():
    """Processo principal de build"""
    print("🚀 Iniciando processo de build...")
    print("=" * 50)
    
    # 1. Validar ambiente
    if not validate_environment():
        print("❌ Build falhou na validação do ambiente")
        return False
    
    # 2. Atualizar versão
    version_info = update_version()
    
    # 3. Executar testes (opcional)
    if '--skip-tests' not in sys.argv:
        if not run_tests():
            print("❌ Build falhou nos testes")
            return False
    else:
        print("⏭️ Testes ignorados (--skip-tests)")
    
    # 4. Validar sintaxe Python
    print("\n🔍 Validando sintaxe Python...")
    python_files = ['app.py', 'version.py', 'cache.py']
    for file in python_files:
        if os.path.exists(file):
            success = run_command(f"python -m py_compile {file}", f"Compilando {file}")
            if not success:
                print(f"❌ Build falhou na validação de sintaxe de {file}")
                return False
    
    # 5. Gerar arquivo de build info
    build_info = {
        **version_info,
        'build_status': 'success',
        'build_type': 'development' if '--dev' in sys.argv else 'production'
    }
    
    with open('build_info.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(build_info, f, indent=2, ensure_ascii=False)
    
    print("\n🎉 Build concluído com sucesso!")
    print("=" * 50)
    print(f"📦 Versão: {version_info['version']}")
    print(f"🏷️ Tag semântica: {version_info['semantic_version']}")
    print(f"📅 Data do build: {version_info['build_date']}")
    print(f"📄 Informações salvas em: build_info.json e version.json")
    
    return True

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1) 