#!/usr/bin/env python3
"""
Script para criar pacote ZIP para deploy no AWS Elastic Beanstalk

COMO USAR:
==========

1. Para gerar um novo pacote de deploy:
   python create_eb_package.py

2. O script irá:
   - Incrementar automaticamente a versão (patch)
   - Criar um arquivo ZIP com timestamp
   - Incluir apenas os arquivos necessários para produção
   - Gerar documentação de deploy (DEPLOY_README.md)

3. Arquivo gerado:
   flask-webscraping-api-v{versao}-{timestamp}.zip

4. Para fazer deploy:
   - Acesse AWS Elastic Beanstalk Console
   - Faça upload do arquivo ZIP gerado
   - Configure variáveis de ambiente conforme DEPLOY_README.md

EXEMPLO:
========
$ python create_eb_package.py
📈 Incrementando versão...
✅ Nova versão: 1.1.4
📦 Criando pacote: flask-webscraping-api-v1.1.4-20250525-220000.zip
✅ Pacote criado com sucesso!

ARQUIVOS INCLUÍDOS:
==================
- application.py (ponto de entrada EB)
- app.py (aplicação Flask)
- requirements.txt (dependências)
- cache/ (sistema de cache)
- .ebextensions/ (configurações EB)
"""

import os
import sys
import zipfile
import shutil
from datetime import datetime
from pathlib import Path
from simple_version import increment_version, read_version

def create_deployment_package():
    """Cria pacote ZIP para deploy no Elastic Beanstalk"""
    
    # Incrementar versão
    print("📈 Incrementando versão...")
    increment_version("patch")
    version = read_version()
    print(f"✅ Nova versão: {version}")
    
    # Nome do arquivo ZIP
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    zip_filename = f"flask-webscraping-api-v{version}-{timestamp}.zip"
    
    print(f"📦 Criando pacote: {zip_filename}")
    
    # Arquivos e pastas a incluir
    files_to_include = [
        'application.py',
        'app.py',
        'requirements.txt',
        'version.txt',
        'simple_version.py',
        'cache/',
        '.ebextensions/'
    ]
    
    # Arquivos a excluir (mesmo que estejam nas pastas incluídas)
    files_to_exclude = {
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.git',
        'venv',
        'env',
        '.env',
        'test_*.py',
        'run_all_tests.py',
        'detailed_test.py',
        'build.py',
        'docker-build.py',
        'docker-deploy.py',
        'deploy.py',
        'eb_deploy.py',
        'Dockerfile',
        'docker-compose.yml',
        '.dockerignore',
        'data',
        'tasks',
        'scripts',
        '.taskmasterconfig',
        '.roomodes',
        '.cursor',
        '.roo',
        '.windsurfrules',
        'postman_collection.json',
        'POSTMAN_GUIDE.md',
        'LICENSE',
        '*.md'
    }
    
    def should_exclude(file_path):
        """Verifica se um arquivo deve ser excluído"""
        path_str = str(file_path)
        name = os.path.basename(path_str)
        
        # Verificar exclusões exatas
        if name in files_to_exclude:
            return True
            
        # Verificar padrões
        if name.startswith('test_') or name.endswith('.pyc') or name.endswith('.pyo'):
            return True
            
        # Manter README.md
        if name == 'README.md':
            return False
            
        # Excluir outros .md
        if name.endswith('.md'):
            return True
            
        # Verificar se está em pasta excluída
        for part in Path(path_str).parts:
            if part in files_to_exclude:
                return True
                
        return False
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            
            # Adicionar arquivos individuais
            for item in files_to_include:
                if os.path.isfile(item):
                    if not should_exclude(item):
                        print(f"  📄 Adicionando arquivo: {item}")
                        zipf.write(item, item)
                
                elif os.path.isdir(item):
                    # Adicionar pasta recursivamente
                    for root, dirs, files in os.walk(item):
                        # Filtrar diretórios
                        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
                        
                        for file in files:
                            file_path = os.path.join(root, file)
                            if not should_exclude(file_path):
                                # Usar caminho relativo no ZIP
                                arcname = os.path.relpath(file_path)
                                print(f"  📄 Adicionando: {arcname}")
                                zipf.write(file_path, arcname)
                else:
                    print(f"⚠️  Item não encontrado: {item}")
        
        # Verificar tamanho do arquivo
        file_size = os.path.getsize(zip_filename)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✅ Pacote criado com sucesso!")
        print(f"📦 Arquivo: {zip_filename}")
        print(f"📏 Tamanho: {file_size_mb:.2f} MB")
        print(f"🏷️  Versão: {version}")
        
        # Listar conteúdo do ZIP
        print(f"\n📋 Conteúdo do pacote:")
        with zipfile.ZipFile(zip_filename, 'r') as zipf:
            for info in zipf.infolist():
                size_kb = info.file_size / 1024
                print(f"  📄 {info.filename} ({size_kb:.1f} KB)")
        
        print(f"\n🚀 Para fazer deploy:")
        print(f"1. Acesse o AWS Elastic Beanstalk Console")
        print(f"2. Crie uma nova aplicação ou selecione uma existente")
        print(f"3. Faça upload do arquivo: {zip_filename}")
        print(f"4. Configure as variáveis de ambiente se necessário")
        
        return zip_filename
        
    except Exception as e:
        print(f"❌ Erro ao criar pacote: {e}")
        return None

def create_readme_for_deployment():
    """Cria um README específico para o deploy"""
    readme_content = f"""# Flask Web Scraping API - Deploy Package

## Informações do Deploy

- **Versão**: {read_version()}
- **Data**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Plataforma**: AWS Elastic Beanstalk
- **Python**: 3.11

## Arquivos Incluídos

- `application.py` - Ponto de entrada para EB
- `app.py` - Aplicação Flask principal
- `requirements.txt` - Dependências Python
- `version.txt` - Versão atual
- `cache/` - Sistema de cache
- `.ebextensions/` - Configurações do Elastic Beanstalk

## Configuração no Elastic Beanstalk

### Variáveis de Ambiente Recomendadas

```
FLASK_ENV=production
SHORT_CACHE_TTL=300
FALLBACK_CACHE_TTL=86400
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Configuração de Instância

- **Tipo recomendado**: t3.micro (Free Tier) ou t3.small
- **Plataforma**: Python 3.11
- **Proxy**: Nginx (padrão)

## Endpoints Disponíveis

- `/heartbeat` - Health check (sem autenticação)
- `/producao` - Dados de produção (com autenticação)
- `/processamento` - Dados de processamento (com autenticação)
- `/comercializacao` - Dados de comercialização (com autenticação)
- `/importacao` - Dados de importação (com autenticação)
- `/exportacao` - Dados de exportação (com autenticação)
- `/apidocs/` - Documentação Swagger

## Autenticação

- **Usuário 1**: user1 / password1
- **Usuário 2**: user2 / password2

## Cache

A aplicação funciona com ou sem Redis:
- **Com Redis**: Cache de alta performance
- **Sem Redis**: Funciona normalmente, mas sem cache

## Monitoramento

Use o endpoint `/heartbeat` para monitoramento:
```bash
curl https://sua-app.elasticbeanstalk.com/heartbeat
```

## Logs

Os logs estão configurados para CloudWatch Logs com retenção de 7 dias.
"""
    
    with open('DEPLOY_README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("📝 Criado DEPLOY_README.md com instruções de deploy")

def main():
    print("🚀 Criando pacote para AWS Elastic Beanstalk...")
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('app.py'):
        print("❌ Erro: app.py não encontrado. Execute este script no diretório raiz do projeto.")
        sys.exit(1)
    
    # Criar README de deploy
    create_readme_for_deployment()
    
    # Criar pacote ZIP
    zip_file = create_deployment_package()
    
    if zip_file:
        print(f"\n🎉 Pacote criado com sucesso: {zip_file}")
        print(f"\n📋 Próximos passos:")
        print(f"1. Acesse: https://console.aws.amazon.com/elasticbeanstalk/")
        print(f"2. Crie uma nova aplicação Python 3.11")
        print(f"3. Faça upload do arquivo: {zip_file}")
        print(f"4. Configure as variáveis de ambiente conforme DEPLOY_README.md")
        print(f"5. Teste o endpoint: https://sua-app.elasticbeanstalk.com/heartbeat")
    else:
        print("❌ Falha ao criar pacote")
        sys.exit(1)

if __name__ == "__main__":
    main() 