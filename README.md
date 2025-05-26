# API Flask de Web Scraping - Dados Vitivinícolas

Esta é uma API Flask que realiza web scraping do site da Embrapa para extrair dados vitivinícolas brasileiros.

## Funcionalidades

- **Autenticação HTTP Basic**: Acesso seguro aos endpoints
- **5 Endpoints de dados**: Produção, Processamento, Comercialização, Importação e Exportação
- **Filtros por ano e sub-opções**: Parâmetros opcionais para refinar consultas
- **Parsing inteligente de tabelas**: Extração estruturada de dados HTML
- **Documentação Swagger**: Interface interativa para testar a API
- **Tratamento de erros**: Logging detalhado e respostas estruturadas

## Configuração do Ambiente

### 1. Criar e Ativar Ambiente Virtual

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

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Executar a Aplicação

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

## Exemplos de Uso

### 1. Usando curl

```bash
# Dados de produção
curl -u user1:password1 "http://localhost:5000/producao"

# Dados de produção filtrados por ano
curl -u user1:password1 "http://localhost:5000/producao?year=2023"

# Dados de exportação com filtros
curl -u user1:password1 "http://localhost:5000/exportacao?year=2023&sub_option=vinhos"

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

# Fazer requisição
response = requests.get(
    'http://localhost:5000/producao',
    auth=auth,
    params={'year': '2023'}
)

data = response.json()
print(data)
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

## Notas Importantes

- A aplicação faz scraping do site oficial da Embrapa
- Respeite os termos de uso do site fonte
- A estrutura das tabelas pode variar dependendo dos dados disponíveis
- Alguns endpoints podem não ter dados para determinados anos ou sub-opções 