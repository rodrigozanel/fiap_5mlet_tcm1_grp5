#!/usr/bin/env python3
"""
Script de build Docker com versionamento automático
Constrói a imagem Docker com informações de versão
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
from version import version_manager

def run_command(command, description, exit_on_error=True):
    """Executa um comando e exibe o resultado"""
    print(f"[BUILD] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[OK] {description} - Sucesso")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} - Erro: {e}")
        if e.stderr:
            print(f"   Erro: {e.stderr.strip()}")
        if exit_on_error:
            sys.exit(1)
        return False, None

def update_version():
    """Atualiza informações de versão"""
    print("[VERSION] Atualizando informações de versão...")
    version_info = version_manager.save_version_file()
    
    print(f"[OK] Versão atualizada:")
    print(f"   Versão: {version_info['version']}")
    print(f"   Versão semântica: {version_info['semantic_version']}")
    print(f"   Build: {version_info['build_number']}")
    print(f"   Commit: {version_info['commit_hash']}")
    print(f"   Branch: {version_info['branch']}")
    
    return version_info

def build_docker_image(version_info, environment='development'):
    """Constrói a imagem Docker com tags de versão"""
    print(f"\n[DOCKER] Construindo imagem Docker...")
    
    # Nome base da imagem
    image_name = "flask-webscraping-api"
    
    # Tags para a imagem
    tags = [
        f"{image_name}:latest",
        f"{image_name}:{version_info['version']}",
        f"{image_name}:{version_info['semantic_version']}",
        f"{image_name}:build-{version_info['build_number']}"
    ]
    
    if environment == 'production':
        tags.append(f"{image_name}:prod-{version_info['version']}")
    else:
        tags.append(f"{image_name}:dev-{version_info['version']}")
    
    # Construir comando docker build com múltiplas tags
    tag_args = " ".join([f"-t {tag}" for tag in tags])
    
    # Build args para passar informações de versão
    build_args = [
        f"--build-arg VERSION={version_info['version']}",
        f"--build-arg SEMANTIC_VERSION={version_info['semantic_version']}",
        f"--build-arg BUILD_NUMBER={version_info['build_number']}",
        f"--build-arg COMMIT_HASH={version_info['commit_hash']}",
        f"--build-arg BRANCH={version_info['branch']}",
        f"--build-arg BUILD_DATE={version_info['build_date']}",
        f"--build-arg ENVIRONMENT={environment}"
    ]
    
    build_cmd = f"docker build {' '.join(build_args)} {tag_args} ."
    
    success, output = run_command(build_cmd, "Construindo imagem Docker")
    
    if success:
        print(f"\n[SUCCESS] Imagem construída com sucesso!")
        print(f"[TAGS] Tags criadas:")
        for tag in tags:
            print(f"   - {tag}")
        
        return tags
    
    return None

def docker_build(environment='development', push=False, registry=None):
    """Processo principal de build Docker"""
    print(f"[START] Iniciando build Docker para ambiente: {environment}")
    print("=" * 60)
    
    # 1. Atualizar versão
    version_info = update_version()
    
    # 2. Construir imagem Docker
    tags = build_docker_image(version_info, environment)
    if not tags:
        return False
    
    # 3. Push para registry (se solicitado)
    if push and registry:
        print(f"\n[PUSH] Fazendo push para registry: {registry}")
        
        for tag in tags:
            # Re-tag para o registry
            registry_tag = f"{registry}/{tag}"
            run_command(f"docker tag {tag} {registry_tag}", f"Re-tagging para {registry_tag}", False)
            run_command(f"docker push {registry_tag}", f"Push {registry_tag}", False)
    
    # 4. Informações finais
    print(f"\n[INFO] Informações do build Docker:")
    print(f"   Versão: {version_info['version']}")
    print(f"   Build: {version_info['build_number']}")
    print(f"   Commit: {version_info['commit_hash']}")
    print(f"   Branch: {version_info['branch']}")
    print(f"   Data: {version_info['build_date']}")
    print(f"   Ambiente: {environment}")
    
    # 5. Comandos úteis
    print(f"\n[SUCCESS] Build Docker concluído com sucesso!")
    print("=" * 60)
    print("Para executar o container:")
    print(f"   docker run -p 5000:5000 {tags[0]}")
    print("\nPara executar com docker-compose:")
    print("   docker-compose up -d")
    print("\nPara verificar a versão:")
    print("   curl http://localhost:5000/heartbeat")
    print("\nPara ver logs:")
    print("   docker-compose logs -f app")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Script de build Docker com versionamento')
    parser.add_argument('--env', choices=['development', 'production'], 
                       default='development', help='Ambiente de build')
    parser.add_argument('--push', action='store_true',
                       help='Fazer push para registry')
    parser.add_argument('--registry', type=str,
                       help='Registry para push (ex: docker.io/username)')
    
    args = parser.parse_args()
    
    success = docker_build(
        environment=args.env,
        push=args.push,
        registry=args.registry
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 