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