#!/usr/bin/env python3
"""
Script para criar pacote ZIP Docker Compose para AWS Elastic Beanstalk
Inclui Flask App + Redis usando docker-compose.yml

COMO USAR:
==========

1. Para gerar pacote Docker Compose:
   python create_multicontainer_package.py

2. O script irá:
   - Incrementar automaticamente a versão
   - Criar ZIP com Dockerfile + docker-compose.yml
   - Incluir apenas arquivos necessários para Docker Compose
   - Gerar documentação específica

3. Arquivo gerado:
   flask-webscraping-api-compose-v{versao}-{timestamp}.zip

4. Para fazer deploy:
   - Acesse AWS Elastic Beanstalk Console
   - Escolha "Docker" como plataforma
   - Upload do arquivo ZIP
   - EB detectará automaticamente Docker Compose

CONTAINERS INCLUÍDOS:
====================
- Flask App (flask-webscraping-api): porta 80 → 5000
- Redis (redis:7.2-alpine): porta 6379, volume persistente
- Logs: CloudWatch automático para ambos containers
- Health Check: /heartbeat endpoint

VANTAGENS DO DOCKER COMPOSE:
============================
- Mais simples que Dockerrun.aws.json v2 (descontinuado)
- Compatível com Elastic Beanstalk moderno
- Sintaxe padrão Docker Compose
- Easier para debug e desenvolvimento local
"""

import os
import json
import zipfile
from datetime import datetime
import shutil

def get_version():
    """Get current version and increment it"""
    try:
        with open('version.txt', 'r') as f:
            version = f.read().strip()
    except FileNotFoundError:
        version = '1.0.0'
    
    # Increment patch version
    parts = version.split('.')
    parts[2] = str(int(parts[2]) + 1)
    new_version = '.'.join(parts)
    
    # Save new version
    with open('version.txt', 'w') as f:
        f.write(new_version)
    
    return new_version

def create_compose_package():
    """Create ZIP package for Docker Compose deployment"""
    
    print("🐳 Flask Web Scraping API - Docker Compose Package Generator")
    print("=" * 80)
    
    # Get version
    print("📈 Incrementando versão...")
    version = get_version()
    print(f"✅ Nova versão: {version}")
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # Package filename
    package_name = f"flask-webscraping-api-compose-v{version}-{timestamp}.zip"
    print(f"📦 Criando pacote Docker Compose: {package_name}")
    
    # Required files for Docker Compose deployment
    required_files = [
        'Dockerfile',
        'docker-compose.yml',
        'application.py',
        'app.py',
        'utils.py',
        'requirements.txt',
        'version.txt',
        'simple_version.py'
    ]
    
    # Additional files and directories to include
    additional_items = [
        'cache/',
        'apis/',
        '.ebextensions/'
    ]
    
    # Arquivos e pastas a incluir
    files_to_include = required_files + additional_items
    
    # Create ZIP file
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        
        # Add required files first
        for file_path in required_files:
            if os.path.exists(file_path):
                zipf.write(file_path, file_path)
                print(f"  📄 Adicionando obrigatório: {file_path}")
            else:
                print(f"  ❌ ERRO: Arquivo obrigatório não encontrado: {file_path}")
                return False
        
        # Add additional files and directories
        for item in additional_items:
            if os.path.exists(item):
                if os.path.isdir(item):
                    # Add directory recursively
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, file_path)
                            print(f"  📄 Adicionando: {file_path}")
                else:
                    # Add single file
                    zipf.write(item, item)
                    print(f"  📄 Adicionando: {item}")
    
    # Get package size
    package_size = os.path.getsize(package_name) / (1024 * 1024)  # MB
    
    print(f"\n✅ Pacote Docker Compose criado com sucesso!")
    print(f"📦 Arquivo: {package_name}")
    print(f"📏 Tamanho: {package_size:.2f} MB")
    print(f"🏷️  Versão: {version}")
    
    # Verify critical files
    print(f"\n🔍 Verificando conteúdo crítico:")
    with zipfile.ZipFile(package_name, 'r') as zipf:
        files_in_zip = zipf.namelist()
        for req_file in required_files:
            if req_file in files_in_zip:
                print(f"  ✅ {req_file}")
            else:
                print(f"  ❌ {req_file}")
    
    # List all files
    print(f"\n📋 Todos os arquivos ({len(files_in_zip)}):")
    with zipfile.ZipFile(package_name, 'r') as zipf:
        for file_info in zipf.filelist:
            size_kb = file_info.file_size / 1024
            print(f"  📄 {file_info.filename} ({size_kb:.1f} KB)")
    
    print(f"\n🚀 Para fazer deploy Docker Compose:")
    print("1. Acesse AWS Elastic Beanstalk Console")
    print("2. Crie nova aplicação ou selecione existente")
    print("3. Plataforma: Docker")
    print(f"4. Upload: {package_name}")
    print("5. EB detectará Docker Compose automaticamente")
    print("6. Aguarde deploy (Redis + Flask App)")
    
    print(f"\n📊 Containers que serão criados:")
    print("  🗄️  Redis: redis:7.2-alpine (128MB)")
    print("  🐍 Flask App: flask-webscraping-api (256MB)")
    print("  🔗 Dependência: flask-app depende do redis")
    print("  💾 Volume: redis_data (persistente)")
    
    # Create README
    create_readme(version, timestamp, package_name)
    
    print("=" * 80)
    print("🎉 PACOTE DOCKER COMPOSE PRONTO PARA DEPLOY!")
    print(f"📦 Arquivo: {package_name}")
    print("🚀 Próximo passo: Upload no AWS Elastic Beanstalk")
    print("=" * 80)
    
    return True

def create_readme(version, timestamp, package_name):
    """Create comprehensive README for the package"""
    readme_content = f"""# Flask Web Scraping API - Docker Compose Package

## Informações do Deploy

- **Versão**: {version}
- **Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Tipo**: Docker Compose (docker-compose.yml)
- **Containers**: Flask App + Redis
- **Arquivo**: {package_name}

## Configuração dos Containers

### Redis Container
- **Imagem**: redis:7.2-alpine
- **Memória**: 128MB (limite), 64MB (reserva)
- **Porta**: 6379
- **Persistência**: Volume redis_data
- **Comando**: redis-server --appendonly yes
- **Logs**: CloudWatch stream prefix 'redis'

### Flask App Container
- **Build**: Dockerfile local
- **Memória**: 256MB (limite), 128MB (reserva)
- **Porta**: 80 (host) → 5000 (container)
- **Dependência**: Aguarda Redis estar disponível
- **Logs**: CloudWatch stream prefix 'flask-app'
- **Health Check**: curl -f http://localhost:5000/heartbeat

## Variáveis de Ambiente

Configuradas automaticamente no container Flask:
- `FLASK_ENV=production`
- `REDIS_HOST=redis`
- `REDIS_PORT=6379`
- `REDIS_DB=0`
- `SHORT_CACHE_TTL=300`
- `FALLBACK_CACHE_TTL=2592000`
- `CSV_FALLBACK_DIR=data/fallback`
- `APP_HOST=0.0.0.0`
- `APP_PORT=5000`

## Deploy no Elastic Beanstalk

1. **Plataforma**: Docker
2. **Detecção**: EB detecta docker-compose.yml automaticamente
3. **Upload**: {package_name}
4. **Aguarde**: 5-10 minutos para deployment

## Logs

Disponíveis no CloudWatch:
- `/aws/elasticbeanstalk/current/application`
  - `redis-*` streams
  - `flask-app-*` streams

## Endpoints para Teste

### Health Check (sem autenticação)
```
GET http://SEU-AMBIENTE.elasticbeanstalk.com/heartbeat
```

### Swagger Docs (sem autenticação)
```
GET http://SEU-AMBIENTE.elasticbeanstalk.com/apidocs/
```

### APIs (com Basic Auth: user1:password1)
```
GET http://SEU-AMBIENTE.elasticbeanstalk.com/producao?year=2023
GET http://SEU-AMBIENTE.elasticbeanstalk.com/comercializacao?year=2023
GET http://SEU-AMBIENTE.elasticbeanstalk.com/processamento?year=2023
GET http://SEU-AMBIENTE.elasticbeanstalk.com/importacao?year=2023
GET http://SEU-AMBIENTE.elasticbeanstalk.com/exportacao?year=2023
```

## Troubleshooting

### Container não inicia
- Verifique logs no CloudWatch
- SSH na instância: `sudo docker-compose logs`

### Redis não conecta
- Verifique se ambos containers estão rodando
- `sudo docker-compose ps`

### API não responde
- Teste health check primeiro
- Verifique autenticação Basic Auth

### Performance
- t3.small recomendado (2GB RAM mínimo)
- Redis + Flask + Sistema = ~2GB total

## Arquitetura

```
Internet → Load Balancer:80 → EC2:80 → Flask Container:5000
                              ↓
                         Redis Container:6379
                              ↓
                         Volume: redis_data
```

## Desenvolvimento Local

Para testar localmente:
```bash
docker-compose up --build
curl http://localhost:80/heartbeat
```
"""
    
    with open(f'COMPOSE_DEPLOY_README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"📖 README criado: COMPOSE_DEPLOY_README.md")

if __name__ == "__main__":
    create_compose_package() 