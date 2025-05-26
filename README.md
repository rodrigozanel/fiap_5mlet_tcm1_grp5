# API Flask de Web Scraping - Dados Vitivinícolas

Esta é uma API Flask que realiza web scraping do site da Embrapa para extrair dados vitivinícolas brasileiros.

## Funcionalidades

- **Autenticação HTTP Basic**: Acesso seguro aos endpoints
- **5 Endpoints de dados**: Produção, Processamento, Comercialização, Importação e Exportação
- **Filtros por ano e sub-opções**: Parâmetros opcionais para refinar consultas
- **Parsing inteligente de tabelas**: Extração estruturada de dados HTML
- **Documentação Swagger**: Interface interativa para testar a API
- **Tratamento de erros**: Logging detalhado e respostas estruturadas
- **Dados de fallback**: Arquivos CSV locais como fonte alternativa de dados

## Configuração do Ambiente

### Opção 1: Docker (Recomendado)

#### Deploy Rápido com Versionamento Automático
```bash
# Deploy completo com rebuild e versionamento
python docker-deploy.py

# Deploy para produção
python docker-deploy.py --env production

# Deploy sem rebuild (usar imagem existente)
python docker-deploy.py --no-rebuild

# Deploy com logs
python docker-deploy.py --logs
```

#### Comandos Docker Manuais
```bash
# Construir imagem com versionamento
python docker-build.py

# Construir para produção
python docker-build.py --env production

# Iniciar com docker-compose
docker-compose up -d

# Ver logs
docker-compose logs -f app

# Parar containers
docker-compose down

# Rebuild completo
docker-compose down && docker-compose build --no-cache && docker-compose up -d
```

#### Verificar Versão no Docker
```bash
# Testar API e ver versão atual
curl http://localhost:5000/heartbeat

# Ver informações da imagem Docker
docker images flask-webscraping-api

# Ver labels da imagem (metadados de versão)
docker inspect flask-webscraping-api:latest
```

### Opção 2: Ambiente Local

#### 1. Criar e Ativar Ambiente Virtual

**Windows:**
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
venv\Scripts\activate
```

**Linux/Mac:**
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
source venv/bin/activate
```

#### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

#### 3. Executar a Aplicação

```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

## Endpoints Disponíveis

### Autenticação
- **Usuário 1**: `user1` / `password1`
- **Usuário 2**: `user2` / `password2`

### Endpoints de Dados

| Endpoint | Descrição | Parâmetros Opcionais | Autenticação |
|----------|-----------|---------------------|---------------|
| `/producao` | Dados de produção | `year`, `sub_option` | ✅ Requerida |
| `/processamento` | Dados de processamento | `year`, `sub_option` | ✅ Requerida |
| `/comercializacao` | Dados de comercialização | `year`, `sub_option` | ✅ Requerida |
| `/importacao` | Dados de importação | `year`, `sub_option` | ✅ Requerida |
| `/exportacao` | Dados de exportação | `year`, `sub_option` | ✅ Requerida |

### Endpoints de Monitoramento

| Endpoint | Descrição | Autenticação |
|----------|-----------|--------------|
| `/` | Informações da API | ❌ Não requerida |
| `/heartbeat` | Health check da API | ❌ Não requerida |
| `/test` | Endpoint de teste | ❌ Não requerida |

### Documentação Swagger
Acesse: `http://localhost:5000/apidocs/`

### Collection Postman
- **Arquivo**: `postman_collection.json`
- **Guia de uso**: `POSTMAN_GUIDE.md`
- **Importar no Postman**: Import > Upload Files > Selecionar `postman_collection.json`

## Parâmetros de Filtro

### Parâmetro `year`
- **Tipo**: Integer
- **Range válido**: 1970-2024
- **Descrição**: Ano para filtrar os dados (válido para todas as APIs)
- **Exemplo**: `?year=2023`

### Parâmetro `sub_option`
- **Tipo**: String
- **Descrição**: Sub-opção específica para cada endpoint
- **Validação**: Lista fechada de valores por endpoint

#### Valores válidos por endpoint:

**`/producao`**
- `VINHO DE MESA`
- `VINHO FINO DE MESA (VINIFERA)`
- `SUCO DE UVA`
- `DERIVADOS`

**`/processamento`**
- `viniferas`
- `americanas`
- `mesa`
- `semclass`

**`/comercializacao`**
- `VINHO DE MESA`
- `ESPUMANTES`
- `UVAS FRESCAS`
- `SUCO DE UVA`

**`/importacao`**
- `vinhos`
- `espumantes`
- `frescas`
- `passas`
- `suco`

**`/exportacao`**
- `vinho`
- `uva`
- `espumantes`
- `suco`

### Validação de Parâmetros
- Parâmetros inválidos retornam erro **HTTP 400** com mensagem explicativa
- Ambos os parâmetros são **opcionais**
- Podem ser usados individualmente ou em combinação

## Exemplos de Uso

### 1. Usando curl

```bash
# Dados de produção (sem filtros)
curl -u user1:password1 "http://localhost:5000/producao"

# Dados de produção filtrados por ano
curl -u user1:password1 "http://localhost:5000/producao?year=2023"

# Dados de produção com sub-opção específica
curl -u user1:password1 "http://localhost:5000/producao?sub_option=VINHO%20DE%20MESA"

# Dados de produção com ambos os filtros
curl -u user1:password1 "http://localhost:5000/producao?year=2023&sub_option=SUCO%20DE%20UVA"

# Dados de processamento com filtros
curl -u user1:password1 "http://localhost:5000/processamento?year=2022&sub_option=viniferas"

# Dados de exportação com filtros
curl -u user1:password1 "http://localhost:5000/exportacao?year=2023&sub_option=vinho"

# Exemplo de erro - ano inválido (retorna HTTP 400)
curl -u user1:password1 "http://localhost:5000/producao?year=1969"

# Exemplo de erro - sub-opção inválida (retorna HTTP 400)
curl -u user1:password1 "http://localhost:5000/producao?sub_option=OPCAO_INEXISTENTE"

# Health check da API (sem autenticação)
curl "http://localhost:5000/heartbeat"

# Informações da API (sem autenticação)
curl "http://localhost:5000/"
```

### 2. Usando Python requests

```python
import requests
from requests.auth import HTTPBasicAuth

# Configurar autenticação
auth = HTTPBasicAuth('user1', 'password1')

# Exemplo 1: Requisição básica sem filtros
response = requests.get(
    'http://localhost:5000/producao',
    auth=auth
)

if response.status_code == 200:
    data = response.json()
    print("Dados de produção:", data)
else:
    print(f"Erro: {response.status_code}")

# Exemplo 2: Requisição com filtros válidos
response = requests.get(
    'http://localhost:5000/producao',
    auth=auth,
    params={
        'year': '2023',
        'sub_option': 'VINHO DE MESA'
    }
)

if response.status_code == 200:
    data = response.json()
    print("Dados filtrados:", data)
else:
    print(f"Erro: {response.status_code}")

# Exemplo 3: Tratamento de erro de validação
response = requests.get(
    'http://localhost:5000/producao',
    auth=auth,
    params={'year': '1969'}  # Ano inválido
)

if response.status_code == 400:
    error_data = response.json()
    print(f"Erro de validação: {error_data['error']}")
elif response.status_code == 200:
    data = response.json()
    print("Dados:", data)

# Exemplo 4: Diferentes endpoints com suas sub-opções
endpoints_examples = {
    'processamento': {'year': '2023', 'sub_option': 'viniferas'},
    'comercializacao': {'year': '2022', 'sub_option': 'ESPUMANTES'},
    'importacao': {'year': '2023', 'sub_option': 'vinhos'},
    'exportacao': {'year': '2023', 'sub_option': 'uva'}
}

for endpoint, params in endpoints_examples.items():
    response = requests.get(
        f'http://localhost:5000/{endpoint}',
        auth=auth,
        params=params
    )
    
    if response.status_code == 200:
        print(f"✅ {endpoint}: Dados obtidos com sucesso")
    else:
        print(f"❌ {endpoint}: Erro {response.status_code}")
```

## Estrutura de Resposta

```json
{
  "data": {
    "header": [
      ["Coluna1", "Coluna2", "Coluna3"]
    ],
    "body": [
      {
        "item_data": ["Item Principal"],
        "sub_items": [
          ["Sub-item 1", "Valor 1"],
          ["Sub-item 2", "Valor 2"]
        ]
      }
    ],
    "footer": [
      ["Total", "Valor Total"]
    ]
  }
}
```

## Dependências Principais

- **Flask**: Framework web
- **requests**: Cliente HTTP para web scraping
- **BeautifulSoup4**: Parser HTML/XML
- **Flask-HTTPAuth**: Autenticação HTTP Basic
- **flasgger**: Documentação Swagger automática

## Versionamento Automático

A aplicação possui um **sistema de versionamento simples** baseado em arquivo que incrementa a versão automaticamente a cada alteração.

### Como Funciona
- **Arquivo de versão**: `version.txt` contém a versão atual (formato: MAJOR.MINOR.PATCH)
- **Incremento automático**: A versão é incrementada automaticamente nos builds
- **Tipos de incremento**: major (X.0.0), minor (X.Y.0), patch (X.Y.Z) - padrão
- **Integração Docker**: Funciona tanto em ambiente local quanto em containers
- **Fallback robusto**: Sistema funciona independente de Git ou outras dependências

### Scripts de Build e Deploy

#### Build Local
```bash
# Build local com incremento patch (padrão)
python build.py --type local

# Build com incremento minor (nova funcionalidade)
python build.py --type local --increment minor

# Build com incremento major (breaking changes)
python build.py --type local --increment major

# Build sem executar testes
python build.py --type local --no-tests
```

#### Build Docker
```bash
# Build Docker com incremento de versão automático
python build.py --type docker

# Build para ambiente de produção
python build.py --type docker --env production --increment minor

# Build para desenvolvimento
python build.py --type docker --env development
```

#### Deploy Completo (Recomendado)
```bash
# Deploy completo: build + deploy + teste
python build.py --type deploy

# Deploy para produção com incremento minor
python build.py --type deploy --env production --increment minor

# Deploy para desenvolvimento
python build.py --type deploy --env development
```

### Gerenciar Versão Manualmente

#### Visualizar Versão
```bash
# Ver versão atual com detalhes
python simple_version.py --show

# Ver apenas o número da versão
cat version.txt

# Ver versão via API
curl http://localhost:5000/heartbeat
```

#### Incrementar Versão
```bash
# Incremento patch: 1.1.0 -> 1.1.1 (correções)
python simple_version.py --increment patch

# Incremento minor: 1.1.0 -> 1.2.0 (novas funcionalidades)
python simple_version.py --increment minor

# Incremento major: 1.1.0 -> 2.0.0 (breaking changes)
python simple_version.py --increment major
```

#### Definir Versão Específica
```bash
# Definir versão específica
python simple_version.py --set 2.0.0

# Resetar para versão inicial
python simple_version.py --set 1.0.0
```

### Verificar Versão em Diferentes Ambientes

#### Local
```bash
# Via script Python
python simple_version.py --show

# Via arquivo
type version.txt  # Windows
cat version.txt   # Linux/Mac
```

#### Docker
```bash
# Via API (container rodando)
curl http://localhost:5000/heartbeat

# Via logs do container
docker-compose logs app | grep -i version

# Via labels da imagem
docker inspect flask-webscraping-api:latest
```

#### API Response
```json
{
  "version": "1.1.0",
  "version_info": {
    "version": "1.1.0",
    "build_date": "2025-01-26T10:30:00.123456",
    "environment": "production",
    "source": "docker"
  }
}
```

### Arquivos do Sistema de Versionamento
- **`version.txt`**: Arquivo principal com a versão atual (ex: 1.1.0)
- **`simple_version.py`**: Script para gerenciar versões manualmente
- **`build.py`**: Script unificado de build que incrementa automaticamente
- **`app.py`**: Aplicação Flask que lê e exibe a versão

### Fluxo de Trabalho Recomendado
1. **Desenvolvimento**: Use `python build.py --type local` para builds locais
2. **Teste**: Use `python build.py --type deploy` para testar em Docker
3. **Produção**: Use `python build.py --type deploy --env production --increment minor`
4. **Hotfix**: Use `python build.py --type deploy --increment patch`

### Vantagens do Sistema Simples
- ✅ **Simplicidade**: Apenas um arquivo `version.txt`
- ✅ **Independência**: Não depende de Git ou ferramentas externas
- ✅ **Automação**: Incremento automático nos builds
- ✅ **Flexibilidade**: Controle manual quando necessário
- ✅ **Integração**: Funciona em local e Docker
- ✅ **Visibilidade**: Versão visível na API e logs

## Desenvolvimento

### Desativar Ambiente Virtual
```bash
deactivate
```

### Atualizar Dependências
```bash
pip freeze > requirements.txt
```

## Logs e Debugging

A aplicação roda em modo debug por padrão. Os logs incluem:
- Erros de requisição HTTP
- Problemas de parsing de tabelas
- Informações sobre tabelas não encontradas

## Testes

### Executar Todos os Testes
```bash
python run_all_tests.py
```

### Testes Individuais
```bash
# Teste de heartbeat e endpoints básicos
python test_heartbeat.py

# Teste de validação de parâmetros
python test_validation.py

# Teste básico da API
python test_api.py

# Teste detalhado da API
python detailed_test.py
```

### Tipos de Teste Disponíveis
- **Heartbeat**: Verifica se a API está funcionando
- **Validação**: Testa as validações de parâmetros `year` e `sub_option`
- **Básico**: Testa todos os endpoints principais
- **Detalhado**: Análise aprofundada da estrutura de resposta

## Notas Importantes

- A aplicação faz scraping do site oficial da Embrapa
- Respeite os termos de uso do site fonte
- A estrutura das tabelas pode variar dependendo dos dados disponíveis
- Alguns endpoints podem não ter dados para determinados anos ou sub-opções
- **Validação rigorosa**: Parâmetros inválidos retornam erro HTTP 400
- **Cache inteligente**: Dados são armazenados em cache para melhor performance 