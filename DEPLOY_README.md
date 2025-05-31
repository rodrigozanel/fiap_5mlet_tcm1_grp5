# Flask Web Scraping API - Deploy Package

## Informações do Deploy

- **Versão**: 1.1.4
- **Data**: 2025-05-25 21:37:48
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
FALLBACK_CACHE_TTL=2592000
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
