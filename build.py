#!/usr/bin/env python3
"""
Script de build simples com incremento de versão
"""

import os
import sys
import subprocess
import argparse
from simple_version import read_version, increment_version, get_version_info

def run_command(command, description):
    """Executa um comando e exibe o resultado"""
    print(f"[BUILD] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[OK] {description} - Sucesso")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} - Erro: {e}")
        if e.stderr:
            print(f"   Erro: {e.stderr.strip()}")
        return False, None

def build_local(increment_type='patch', run_tests=True):
    """Build local com incremento de versão"""
    print("[START] Iniciando build local")
    print("=" * 50)
    
    # 1. Mostrar versão atual
    current_version = read_version()
    print(f"[INFO] Versão atual: {current_version}")
    
    # 2. Executar testes (se solicitado)
    if run_tests:
        print("\n[TEST] Executando testes...")
        success, _ = run_command("python -m pytest", "Executando testes")
        if not success:
            print("[WARN] Testes falharam, mas continuando...")
    
    # 3. Incrementar versão
    print(f"\n[VERSION] Incrementando versão ({increment_type})...")
    new_version = increment_version(increment_type)
    print(f"[OK] Versão atualizada: {current_version} -> {new_version}")
    
    # 4. Informações finais
    version_info = get_version_info()
    print(f"\n[SUCCESS] Build local concluído!")
    print("=" * 50)
    print(f"Nova versão: {version_info['version']}")
    print(f"Data do build: {version_info['build_date']}")
    print(f"Arquivo de versão: {version_info['version_file']}")
    
    return True

def build_docker(increment_type='patch', environment='development'):
    """Build Docker com incremento de versão"""
    print("[START] Iniciando build Docker")
    print("=" * 50)
    
    # 1. Incrementar versão
    current_version = read_version()
    print(f"[INFO] Versão atual: {current_version}")
    
    print(f"\n[VERSION] Incrementando versão ({increment_type})...")
    new_version = increment_version(increment_type)
    print(f"[OK] Versão atualizada: {current_version} -> {new_version}")
    
    # 2. Build Docker
    print(f"\n[DOCKER] Construindo imagem Docker...")
    
    # Nome da imagem
    image_name = "flask-webscraping-api"
    
    # Tags
    tags = [
        f"{image_name}:latest",
        f"{image_name}:{new_version}",
        f"{image_name}:{environment}-{new_version}"
    ]
    
    # Comando de build
    tag_args = " ".join([f"-t {tag}" for tag in tags])
    build_args = [
        f"--build-arg VERSION={new_version}",
        f"--build-arg BUILD_DATE={get_version_info()['build_date']}",
        f"--build-arg ENVIRONMENT={environment}"
    ]
    
    build_cmd = f"docker build {' '.join(build_args)} {tag_args} ."
    
    success, _ = run_command(build_cmd, "Construindo imagem Docker")
    
    if success:
        print(f"\n[SUCCESS] Build Docker concluído!")
        print("=" * 50)
        print(f"Nova versão: {new_version}")
        print("Tags criadas:")
        for tag in tags:
            print(f"   - {tag}")
        print("\nPara testar:")
        print(f"   docker run -p 5000:5000 {tags[0]}")
        return True
    else:
        return False

def deploy_docker(increment_type='patch', environment='development'):
    """Deploy Docker completo"""
    print("[START] Iniciando deploy Docker completo")
    print("=" * 50)
    
    # 1. Build com incremento de versão
    if not build_docker(increment_type, environment):
        print("[ERROR] Falha no build Docker")
        return False
    
    # 2. Parar containers existentes
    print(f"\n[DEPLOY] Parando containers existentes...")
    run_command("docker-compose down", "Parando containers")
    
    # 3. Iniciar novos containers
    print(f"\n[DEPLOY] Iniciando containers...")
    success, _ = run_command("docker-compose up -d", "Iniciando containers")
    
    if success:
        print(f"\n[WAIT] Aguardando containers ficarem prontos...")
        run_command("timeout 10", "Aguardando inicialização")
        
        # 4. Testar API
        print(f"\n[TEST] Testando API...")
        success, output = run_command("curl -s http://localhost:5000/heartbeat", "Teste de heartbeat")
        
        if success and output:
            try:
                import json
                data = json.loads(output)
                print(f"[OK] API respondendo!")
                print(f"   Versão: {data.get('version', 'unknown')}")
                print(f"   Ambiente: {data.get('version_info', {}).get('environment', 'unknown')}")
                print(f"   Docker: {data.get('docker', {}).get('running_in_docker', False)}")
            except:
                print(f"[WARN] API respondeu mas formato inesperado")
        
        print(f"\n[SUCCESS] Deploy concluído!")
        print("=" * 50)
        print("API disponível em: http://localhost:5000")
        print("Documentação: http://localhost:5000/apidocs/")
        return True
    
    return False

def main():
    parser = argparse.ArgumentParser(description='Script de build simples')
    parser.add_argument('--type', choices=['local', 'docker', 'deploy'], 
                       default='local', help='Tipo de build')
    parser.add_argument('--increment', choices=['major', 'minor', 'patch'], 
                       default='patch', help='Tipo de incremento de versão')
    parser.add_argument('--env', choices=['development', 'production'], 
                       default='development', help='Ambiente')
    parser.add_argument('--no-tests', action='store_true',
                       help='Pular testes no build local')
    
    args = parser.parse_args()
    
    if args.type == 'local':
        success = build_local(args.increment, not args.no_tests)
    elif args.type == 'docker':
        success = build_docker(args.increment, args.env)
    elif args.type == 'deploy':
        success = deploy_docker(args.increment, args.env)
    else:
        print("Tipo de build inválido")
        success = False
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 