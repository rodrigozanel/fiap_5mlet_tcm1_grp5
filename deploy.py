#!/usr/bin/env python3
"""
Script de deploy automatizado
Executa build, testes e deploy da aplicação
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

def run_command(command, description, exit_on_error=True):
    """Executa um comando e exibe o resultado"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Sucesso")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erro: {e}")
        if e.stderr:
            print(f"   Erro: {e.stderr.strip()}")
        if exit_on_error:
            sys.exit(1)
        return False, None

def deploy(environment='development', skip_tests=False, auto_commit=False):
    """Processo principal de deploy"""
    print(f"🚀 Iniciando deploy para ambiente: {environment}")
    print("=" * 60)
    
    # 1. Executar build
    build_cmd = "python build.py"
    if skip_tests:
        build_cmd += " --skip-tests"
    if environment == 'development':
        build_cmd += " --dev"
    
    success, _ = run_command(build_cmd, "Executando build")
    if not success:
        return False
    
    # 2. Commit automático (se solicitado)
    if auto_commit:
        print("\n📝 Fazendo commit automático...")
        
        # Adicionar arquivos de versão
        run_command("git add version.json build_info.json", "Adicionando arquivos de versão", False)
        
        # Verificar se há mudanças para commit
        success, output = run_command("git status --porcelain", "Verificando mudanças", False)
        if success and output.strip():
            # Obter informações de versão para o commit
            try:
                import json
                with open('version.json', 'r') as f:
                    version_info = json.load(f)
                
                commit_msg = f"build: Deploy versão {version_info['version']} (build {version_info['build_number']})"
                run_command(f'git commit -m "{commit_msg}"', "Fazendo commit", False)
            except:
                run_command('git commit -m "build: Deploy automático"', "Fazendo commit", False)
        else:
            print("   Nenhuma mudança para commit")
    
    # 3. Informações finais
    print("\n📊 Informações do deploy:")
    try:
        import json
        with open('version.json', 'r') as f:
            version_info = json.load(f)
        
        print(f"   🏷️ Versão: {version_info['version']}")
        print(f"   📦 Build: {version_info['build_number']}")
        print(f"   🔗 Commit: {version_info['commit_hash']}")
        print(f"   🌿 Branch: {version_info['branch']}")
        print(f"   📅 Data: {version_info['build_date']}")
        print(f"   🎯 Ambiente: {environment}")
    except:
        print("   ⚠️ Não foi possível carregar informações de versão")
    
    # 4. Instruções de execução
    print(f"\n🎉 Deploy concluído com sucesso!")
    print("=" * 60)
    print("📋 Para executar a aplicação:")
    print("   python app.py")
    print("\n📋 Para verificar a versão:")
    print("   curl http://localhost:5000/heartbeat")
    print("\n📋 Para acessar a documentação:")
    print("   http://localhost:5000/apidocs/")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Script de deploy automatizado')
    parser.add_argument('--env', choices=['development', 'production'], 
                       default='development', help='Ambiente de deploy')
    parser.add_argument('--skip-tests', action='store_true', 
                       help='Pular execução de testes')
    parser.add_argument('--auto-commit', action='store_true',
                       help='Fazer commit automático dos arquivos de versão')
    
    args = parser.parse_args()
    
    success = deploy(
        environment=args.env,
        skip_tests=args.skip_tests,
        auto_commit=args.auto_commit
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 