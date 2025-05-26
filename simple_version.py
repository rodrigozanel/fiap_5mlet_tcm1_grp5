#!/usr/bin/env python3
"""
Sistema de versionamento simples baseado em arquivo version.txt
"""

import os
from datetime import datetime

VERSION_FILE = "version.txt"

def read_version():
    """Lê a versão atual do arquivo version.txt"""
    if not os.path.exists(VERSION_FILE):
        # Se não existe, cria com versão inicial
        write_version("1.0.0")
        return "1.0.0"
    
    try:
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            version = f.read().strip()
            return version if version else "1.0.0"
    except Exception:
        return "1.0.0"

def write_version(version):
    """Escreve a versão no arquivo version.txt"""
    try:
        with open(VERSION_FILE, 'w', encoding='utf-8') as f:
            f.write(version)
        return True
    except Exception as e:
        print(f"Erro ao escrever versão: {e}")
        return False

def increment_version(version_type='patch'):
    """
    Incrementa a versão baseado no tipo
    version_type: 'major', 'minor', 'patch'
    """
    current = read_version()
    
    try:
        # Parse da versão atual (formato: MAJOR.MINOR.PATCH)
        parts = current.split('.')
        major = int(parts[0]) if len(parts) > 0 else 1
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        
        # Incrementa baseado no tipo
        if version_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif version_type == 'minor':
            minor += 1
            patch = 0
        else:  # patch (padrão)
            patch += 1
        
        new_version = f"{major}.{minor}.{patch}"
        
        if write_version(new_version):
            return new_version
        else:
            return current
            
    except Exception as e:
        print(f"Erro ao incrementar versão: {e}")
        return current

def get_version_info():
    """Retorna informações completas da versão"""
    version = read_version()
    
    return {
        'version': version,
        'build_date': datetime.now().isoformat(),
        'version_file': VERSION_FILE
    }

def main():
    """Função principal para uso via linha de comando"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerenciador de versão simples')
    parser.add_argument('--increment', choices=['major', 'minor', 'patch'], 
                       help='Incrementar versão')
    parser.add_argument('--set', type=str, help='Definir versão específica')
    parser.add_argument('--show', action='store_true', help='Mostrar versão atual')
    
    args = parser.parse_args()
    
    if args.increment:
        old_version = read_version()
        new_version = increment_version(args.increment)
        print(f"Versão incrementada: {old_version} -> {new_version}")
    elif args.set:
        if write_version(args.set):
            print(f"Versão definida para: {args.set}")
        else:
            print("Erro ao definir versão")
    else:
        # Mostrar versão atual (padrão)
        info = get_version_info()
        print(f"Versão atual: {info['version']}")
        print(f"Data de build: {info['build_date']}")
        print(f"Arquivo: {info['version_file']}")

if __name__ == "__main__":
    main() 