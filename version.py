#!/usr/bin/env python3
"""
Módulo de versionamento automático baseado em Git
Gera versões no formato: MAJOR.MINOR.PATCH-COMMITS-HASH
"""

import subprocess
import os
import json
from datetime import datetime

class VersionManager:
    def __init__(self, base_version="1.0.0"):
        self.base_version = base_version
        self.version_file = "version.json"
        
    def get_git_info(self):
        """Obtém informações do Git"""
        try:
            # Número de commits desde o último tag
            commit_count = subprocess.check_output(
                ['git', 'rev-list', '--count', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            # Hash do commit atual (curto)
            commit_hash = subprocess.check_output(
                ['git', 'rev-parse', '--short', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            # Branch atual
            branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            # Data do último commit
            commit_date = subprocess.check_output(
                ['git', 'log', '-1', '--format=%ci'],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            return {
                'commit_count': int(commit_count),
                'commit_hash': commit_hash,
                'branch': branch,
                'commit_date': commit_date
            }
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def get_version_info(self):
        """Gera informações completas de versão"""
        git_info = self.get_git_info()
        
        if git_info:
            # Versão no formato: MAJOR.MINOR.PATCH.COMMITS
            version = f"{self.base_version}.{git_info['commit_count']}"
            
            # Versão semântica com hash
            semantic_version = f"{self.base_version}-{git_info['commit_count']}-g{git_info['commit_hash']}"
            
            version_info = {
                'version': version,
                'semantic_version': semantic_version,
                'build_number': git_info['commit_count'],
                'commit_hash': git_info['commit_hash'],
                'branch': git_info['branch'],
                'commit_date': git_info['commit_date'],
                'build_date': datetime.now().isoformat(),
                'is_git_repo': True
            }
        else:
            # Fallback quando Git não está disponível
            version_info = {
                'version': self.base_version,
                'semantic_version': self.base_version,
                'build_number': 0,
                'commit_hash': 'unknown',
                'branch': 'unknown',
                'commit_date': 'unknown',
                'build_date': datetime.now().isoformat(),
                'is_git_repo': False
            }
        
        return version_info
    
    def save_version_file(self):
        """Salva informações de versão em arquivo JSON"""
        version_info = self.get_version_info()
        
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(version_info, f, indent=2, ensure_ascii=False)
        
        return version_info
    
    def load_version_file(self):
        """Carrega informações de versão do arquivo JSON"""
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Se não conseguir carregar, gera nova versão
        return self.save_version_file()

# Instância global
version_manager = VersionManager()

def get_version():
    """Função conveniente para obter versão atual"""
    return version_manager.get_version_info()

def get_simple_version():
    """Retorna apenas o número da versão"""
    return version_manager.get_version_info()['version']

if __name__ == "__main__":
    # Teste do módulo
    info = version_manager.save_version_file()
    print("Informações de versão:")
    for key, value in info.items():
        print(f"  {key}: {value}") 