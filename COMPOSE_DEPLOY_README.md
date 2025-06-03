# Flask Web Scraping API - Docker Compose Package

## Informações do Deploy

- **Versão**: 1.1.16
- **Data**: 2025-06-02 18:21:20
- **Tipo**: Docker Compose (docker-compose.yml)
- **Containers**: Flask App + Redis
- **Arquivo**: flask-webscraping-api-compose-v1.1.16-20250602-182120.zip

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
3. **Upload**: flask-webscraping-api-compose-v1.1.16-20250602-182120.zip
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
