#!/usr/bin/env python3
"""
Script de deploy Docker simplificado
Reconstrói e reinicia os containers com nova versão
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

def run_command(command, description, exit_on_error=True):
    """Executa um comando e exibe o resultado"""
    print(f"[DEPLOY] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[OK] {description} - Sucesso")
        if result.stdout.strip():
            # Mostrar apenas as últimas linhas para evitar spam
            lines = result.stdout.strip().split('\n')
            if len(lines) > 5:
                print(f"   ... ({len(lines)} linhas)")
                for line in lines[-3:]:
                    print(f"   {line}")
            else:
                for line in lines:
                    print(f"   {line}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} - Erro: {e}")
        if e.stderr:
            print(f"   Erro: {e.stderr.strip()}")
        if exit_on_error:
            sys.exit(1)
        return False, None

def docker_deploy(environment='development', rebuild=True, logs=False):
    """Deploy Docker com docker-compose"""
    print(f"[START] Iniciando deploy Docker com docker-compose")
    print(f"[ENV] Ambiente: {environment}")
    print("=" * 60)
    
    # 1. Parar containers existentes
    print("\n[STOP] Parando containers existentes...")
    run_command("docker-compose down", "Parando containers", False)
    
    # 2. Rebuild da imagem (se solicitado)
    if rebuild:
        print("\n[BUILD] Reconstruindo imagem...")
        
        # Primeiro, executar o build com versionamento
        build_cmd = f"python docker-build.py --env {environment}"
        success, _ = run_command(build_cmd, "Executando build com versionamento")
        
        if not success:
            print("[FALLBACK] Falha no build com versionamento, tentando build direto...")
            run_command("docker-compose build --no-cache", "Build direto com docker-compose")
    
    # 3. Iniciar containers
    print("\n[START] Iniciando containers...")
    run_command("docker-compose up -d", "Iniciando containers")
    
    # 4. Aguardar containers ficarem prontos
    print("\n[WAIT] Aguardando containers ficarem prontos...")
    run_command("sleep 10", "Aguardando inicialização", False)
    
    # 5. Verificar status
    print("\n[STATUS] Verificando status dos containers...")
    run_command("docker-compose ps", "Status dos containers", False)
    
    # 6. Testar API
    print("\n[TEST] Testando API...")
    success, output = run_command("curl -s http://localhost:5000/heartbeat", "Teste de heartbeat", False)
    
    if success and output:
        try:
            import json
            data = json.loads(output)
            print(f"   [OK] API respondendo!")
            print(f"   Versão: {data.get('version', 'unknown')}")
            print(f"   Versão semântica: {data.get('semantic_version', 'unknown')}")
            print(f"   Commit: {data.get('build_info', {}).get('commit_hash', 'unknown')}")
            print(f"   Docker: {data.get('docker', {}).get('running_in_docker', False)}")
        except:
            print(f"   [WARN] API respondeu mas formato inesperado: {output[:100]}...")
    else:
        print("   [ERROR] API não está respondendo")
    
    # 7. Mostrar logs (se solicitado)
    if logs:
        print("\n[LOGS] Logs dos containers:")
        run_command("docker-compose logs --tail=20", "Logs recentes", False)
    
    # 8. Informações finais
    print(f"\n[SUCCESS] Deploy concluído!")
    print("=" * 60)
    print("Comandos úteis:")
    print("   docker-compose logs -f app     # Ver logs em tempo real")
    print("   docker-compose ps              # Status dos containers")
    print("   docker-compose down            # Parar containers")
    print("   curl http://localhost:5000/heartbeat  # Testar API")
    print("   http://localhost:5000/apidocs/        # Documentação Swagger")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Deploy Docker com docker-compose')
    parser.add_argument('--env', choices=['development', 'production'], 
                       default='development', help='Ambiente de deploy')
    parser.add_argument('--no-rebuild', action='store_true',
                       help='Não reconstruir a imagem')
    parser.add_argument('--logs', action='store_true',
                       help='Mostrar logs após o deploy')
    
    args = parser.parse_args()
    
    success = docker_deploy(
        environment=args.env,
        rebuild=not args.no_rebuild,
        logs=args.logs
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 