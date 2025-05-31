# Guia de Deploy - AWS Elastic Beanstalk

Este guia mostra como fazer deploy da API Flask no AWS Elastic Beanstalk usando o console web.

## 📦 Passo 0: Gerar Pacote de Deploy

**ANTES DE FAZER O DEPLOY**, você precisa gerar o pacote ZIP:

```bash
# Execute no diretório do projeto
python create_eb_package.py
```

**Saída esperada:**
```
📈 Incrementando versão...
✅ Nova versão: 1.1.4
📦 Criando pacote: flask-webscraping-api-v1.1.4-20250525-220000.zip
📏 Tamanho: 0.01 MB
✅ Pacote criado com sucesso!
```

**Arquivo gerado:** `flask-webscraping-api-v{versao}-{timestamp}.zip`

> ⚠️ **IMPORTANTE**: Use sempre o arquivo ZIP mais recente gerado pelo script!

---

## 📋 Pré-requisitos

- ✅ Conta AWS ativa
- ✅ **Pacote ZIP gerado** (execute `python create_eb_package.py`)
- ✅ Acesso ao console AWS

## 🚀 Passo a Passo do Deploy

### 1. Acessar o Console AWS

1. Acesse: https://console.aws.amazon.com/
2. Faça login na sua conta AWS
3. Na barra de pesquisa, digite "Elastic Beanstalk"
4. Clique em "AWS Elastic Beanstalk"

### 2. Criar Nova Aplicação

1. Clique em **"Create application"**
2. Preencha os dados:
   - **Application name**: `flask-webscraping-api`
   - **Application tags** (opcional): 
     - Key: `Project`, Value: `FIAP-WebScraping`
     - Key: `Environment`, Value: `Production`

### 3. Configurar Ambiente

1. **Environment tier**: Web server environment (padrão)
2. **Environment information**:
   - **Environment name**: `flask-webscraping-api-prod`
   - **Domain**: deixe em branco (será gerado automaticamente)
3. **Platform**:
   - **Platform**: Python
   - **Platform branch**: Python 3.11 running on 64bit Amazon Linux 2023
   - **Platform version**: (use a mais recente)

### 4. Upload do Código

1. **Application code**: 
   - Selecione **"Upload your code"**
   - **Source code origin**: Local file
   - Clique em **"Choose file"**
   - Selecione o arquivo: `flask-webscraping-api-v1.1.3-20250525-212648.zip`
   - **Version label**: `v1.1.3-20250525-212648` (ou deixe automático)

### 5. Configurar Preset (Opcional)

1. **Presets**: 
   - Selecione **"Single instance (free tier eligible)"** para economia
   - Ou **"High availability"** para produção

### 6. Configurações Avançadas (Recomendado)

Clique em **"Configure more options"** para configurações detalhadas:

#### 6.1 Software
- **Environment properties** (variáveis de ambiente):
  ```
  FLASK_ENV = production
  SHORT_CACHE_TTL = 300
  FALLBACK_CACHE_TTL = 2592000
  REDIS_HOST = localhost
  REDIS_PORT = 6379
  REDIS_DB = 0
  ```

#### 6.2 Instances
- **Instance types**: t3.micro (Free Tier) ou t3.small
- **AMI ID**: (deixe padrão)

#### 6.3 Capacity
- **Environment type**: Single instance (para Free Tier)
- Ou **Load balanced** (para produção)

#### 6.4 Load balancer (se escolheu Load balanced)
- **Load balancer type**: Application Load Balancer
- **Listeners**: HTTP:80

#### 6.5 Rolling updates and deployments
- **Deployment policy**: All at once (mais rápido)
- **Batch size**: 30%

#### 6.6 Security
- **Service role**: aws-elasticbeanstalk-service-role (será criado automaticamente)
- **EC2 key pair**: (opcional, para SSH)
- **IAM instance profile**: aws-elasticbeanstalk-ec2-role

#### 6.7 Monitoring
- **Health reporting**: Enhanced
- **Health check URL**: `/heartbeat`
- **Ignore HTTP 4xx**: No

#### 6.8 Managed updates
- **Managed platform updates**: Enabled
- **Update level**: Minor and patch
- **Maintenance window**: (escolha um horário de baixo tráfego)

#### 6.9 Notifications
- **Email**: (seu email para notificações)

### 7. Criar Ambiente

1. Revise todas as configurações
2. Clique em **"Create environment"**
3. Aguarde o deploy (pode levar 5-10 minutos)

## 📊 Verificação do Deploy

### 1. Status do Ambiente

Aguarde até que o status seja **"Ok"** (verde).

### 2. Testar a Aplicação

1. Clique na URL do ambiente (ex: `http://flask-webscraping-api-prod.us-east-1.elasticbeanstalk.com`)
2. Teste o endpoint de health check:
   ```bash
   curl http://sua-url.elasticbeanstalk.com/heartbeat
   ```

### 3. Testar Endpoints com Autenticação

```bash
# Teste endpoint de produção
curl -u user1:password1 "http://sua-url.elasticbeanstalk.com/producao?year=2023"

# Teste documentação Swagger
# Acesse: http://sua-url.elasticbeanstalk.com/apidocs/
```

## 🔧 Configurações Pós-Deploy

### 1. Configurar Domínio Personalizado (Opcional)

1. No console EB, vá em **"Configuration"**
2. Clique em **"Edit"** na seção **"Load balancer"**
3. Adicione listeners HTTPS se necessário
4. Configure certificado SSL via AWS Certificate Manager

### 2. Configurar Redis (Opcional)

Para melhor performance, configure ElastiCache Redis:

1. Vá para o console ElastiCache
2. Crie um cluster Redis
3. Atualize as variáveis de ambiente:
   - `REDIS_HOST`: endpoint do cluster
   - `REDIS_PORT`: 6379

### 3. Configurar Logs

1. No console EB, vá em **"Configuration"**
2. Seção **"Software"** > **"Edit"**
3. **Log Options**:
   - **Instance log streaming to CloudWatch Logs**: Enabled
   - **Retention**: 7 days
   - **Lifecycle**: Delete logs when environment is terminated

### 4. Configurar Monitoramento

1. **CloudWatch Alarms**:
   - CPU Utilization > 80%
   - Application requests > 1000/min
   - Application latency > 5s

2. **Health Dashboard**:
   - Configure alertas por email
   - Monitore métricas de aplicação

## 🔄 Atualizações Futuras

### Deploy de Nova Versão

**Passo a passo completo:**

1. **Gerar novo pacote:**
   ```bash
   # No diretório do projeto
   python create_eb_package.py
   ```
   
2. **Verificar arquivo gerado:**
   ```bash
   # Exemplo de saída
   ✅ Pacote criado: flask-webscraping-api-v1.1.5-20250525-230000.zip
   ```

3. **Fazer deploy no AWS:**
   - Acesse o console Elastic Beanstalk
   - Selecione seu ambiente
   - Clique em **"Upload and deploy"**
   - Selecione o arquivo ZIP recém-criado
   - Aguarde o deploy (3-5 minutos)

4. **Verificar deploy:**
   ```bash
   # Teste o health check
   curl https://sua-app.elasticbeanstalk.com/heartbeat
   ```

> 💡 **Dica**: O script incrementa automaticamente a versão a cada execução!

### Rollback

1. No console EB, vá em **"Application versions"**
2. Selecione uma versão anterior
3. Clique em **"Deploy"**

## 💰 Custos Estimados

### Free Tier (t3.micro)
- **EC2**: Gratuito (750 horas/mês)
- **Load Balancer**: ~$16/mês (se usado)
- **CloudWatch**: Gratuito (básico)

### Produção (t3.small)
- **EC2**: ~$15/mês
- **Load Balancer**: ~$16/mês
- **ElastiCache**: ~$15/mês (cache.t3.micro)

## 🚨 Troubleshooting

### Problemas Comuns

1. **Deploy falha**:
   - Verifique logs em **"Logs"** > **"Request logs"**
   - Verifique se `application.py` está no root do ZIP

2. **Aplicação não responde**:
   - Verifique health check em `/heartbeat`
   - Verifique variáveis de ambiente

3. **Erro 502 Bad Gateway**:
   - Aplicação não está rodando na porta correta
   - Verifique logs da aplicação

4. **Dependências não instaladas**:
   - Verifique `requirements.txt`
   - Verifique logs de deploy

### Comandos Úteis

```bash
# Testar localmente antes do deploy
python application.py

# Verificar conteúdo do ZIP
unzip -l flask-webscraping-api-v1.1.3-20250525-212648.zip

# Testar endpoints
curl -u user1:password1 "http://localhost:5000/heartbeat"
```

## 📞 Suporte

- **AWS Documentation**: https://docs.aws.amazon.com/elasticbeanstalk/
- **AWS Support**: Console AWS > Support
- **Community**: AWS Forums

---

**✅ Deploy concluído com sucesso!**

Sua API Flask está agora rodando no AWS Elastic Beanstalk com:
- ✅ Autenticação HTTP Basic
- ✅ 5 endpoints de dados vitivinícolas
- ✅ Sistema de cache inteligente
- ✅ Documentação Swagger
- ✅ Monitoramento e logs
- ✅ Versionamento automático 