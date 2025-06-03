# 🔗 Como Encontrar o Endereço do Load Balancer

## 🎯 Método 1: Console AWS Elastic Beanstalk (MAIS FÁCIL)

### Passo a Passo:
1. **Acesse AWS Console** → **Elastic Beanstalk**
2. **Clique no seu environment**: `flask-vitivinicola-api-env`
3. **Na página principal do environment**, procure por:
   - **Environment URL** (canto superior direito)
   - OU **Go to environment** (botão azul)

### O que você deve ver:
```
Environment URL: http://flask-vitivinicola-api-env.eba-h8ms2mq2.us-east-2.elasticbeanstalk.com
```

**⚠️ IMPORTANTE**: Este é o endereço CORRETO para acessar sua aplicação!

---

## 🔧 Método 2: Console EC2 Load Balancers

### Se o método 1 não funcionar:

1. **AWS Console** → **EC2** → **Load Balancers** (menu lateral esquerdo)
2. **Procure pelo Load Balancer** com nome similar a:
   - `awseb-AWSEB-xxxxxxxxxxxxx`
   - Ou que tenha tag `elasticbeanstalk:environment-name = flask-vitivinicola-api-env`
3. **Copie o DNS name**:
   ```
   awseb-AWSEB-1234567890-123456789.us-east-2.elb.amazonaws.com
   ```

---

## 🖥️ Método 3: EB CLI (Linha de Comando)

Se você tem EB CLI instalado:

```bash
# No diretório do seu projeto
eb status

# OU para ver apenas a URL
eb status | grep "CNAME"
```

**Output esperado:**
```
Environment details for: flask-vitivinicola-api-env
  Application name: flask-vitivinicola-api
  Region: us-east-2
  CNAME: flask-vitivinicola-api-env.eba-h8ms2mq2.us-east-2.elasticbeanstalk.com
```

---

## 🖥️ Método 4: AWS CLI

```bash
# Instalar AWS CLI se não tiver
pip install awscli

# Configurar (se não configurado)
aws configure

# Buscar environment
aws elasticbeanstalk describe-environments \
  --environment-names flask-vitivinicola-api-env \
  --region us-east-2 \
  --query 'Environments[0].CNAME' \
  --output text
```

---

## 🧪 Testando o Endereço Correto

### Formato do endereço:
```
http://ENVIRONMENT_NAME.RANDOM_ID.REGION.elasticbeanstalk.com
```

### Exemplo real:
```
http://flask-vitivinicola-api-env.eba-h8ms2mq2.us-east-2.elasticbeanstalk.com
```

### Teste básico:
```bash
# Teste de conectividade
curl -I http://SEU_LOAD_BALANCER_URL/heartbeat

# Se funcionar, você verá algo como:
HTTP/1.1 200 OK
Content-Type: application/json
```

---

## ❌ ERROS COMUNS

### ❌ Usar IP da Instância EC2
```bash
# ERRADO - não use o IP da instância
curl http://3.145.123.45/heartbeat
# Isso não funciona porque o tráfego deve passar pelo Load Balancer
```

### ❌ Usar HTTPS sem certificado
```bash
# ERRADO - se não configurou SSL
curl https://your-app.elasticbeanstalk.com/heartbeat
# Use HTTP em vez de HTTPS
```

### ❌ URL malformada
```bash
# ERRADO - barras extras
curl http://your-app.elasticbeanstalk.com//heartbeat

# CORRETO
curl http://your-app.elasticbeanstalk.com/heartbeat
```

---

## 🔍 Verificação de Status

### Se encontrou o Load Balancer, verifique:

1. **Health Check do Target Group**:
   - AWS Console → EC2 → Target Groups
   - Procure pelo target group do seu environment
   - Verifique se targets estão "healthy"

2. **Status do Load Balancer**:
   - AWS Console → EC2 → Load Balancers
   - Status deve ser "active"
   - Scheme deve ser "internet-facing"

3. **Security Groups**:
   - Load Balancer deve ter porta 80 aberta (0.0.0.0/0)
   - Instâncias devem aceitar tráfego do Load Balancer

---

## 🚀 Script de Teste Automatizado

Crie um arquivo `test_lb.py`:

```python
import requests
import sys

def test_load_balancer(url):
    """Testa se o Load Balancer está respondendo"""
    print(f"🔍 Testando Load Balancer: {url}")
    
    try:
        # Teste simples de conectividade
        response = requests.get(f"{url}/heartbeat", timeout=10)
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Tempo: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            print("🎉 Load Balancer está funcionando!")
            return True
        else:
            print(f"⚠️  Load Balancer responde mas com erro: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Não consegue conectar ao Load Balancer")
        print("   Verifique se a URL está correta")
        return False
    except requests.exceptions.Timeout:
        print("⏰ Load Balancer muito lento (timeout)")
        return False

if __name__ == "__main__":
    # Substitua pela sua URL
    lb_url = "http://flask-vitivinicola-api-env.eba-h8ms2mq2.us-east-2.elasticbeanstalk.com"
    test_load_balancer(lb_url)
```

---

## 📱 RESUMO RÁPIDO

1. **Console EB** → **Environment** → **Environment URL** ← **USE ESTE**
2. **Teste**: `curl http://SUA_URL/heartbeat`
3. **Se não funcionar**: Verifique Target Group health
4. **Nunca use**: IP da instância EC2 diretamente

**🎯 O endereço que você passou está correto:**
```
http://flask-vitivinicola-api-env.eba-h8ms2mq2.us-east-2.elasticbeanstalk.com
```

**O problema não é a URL, é que a aplicação não está respondendo no Load Balancer.** 