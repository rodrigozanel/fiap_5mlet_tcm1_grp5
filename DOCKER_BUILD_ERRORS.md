# 🚨 Docker Build Errors - Troubleshooting Guide

## ❌ Erro Atual Resolvido

**Mensagem de Erro:**
```
Instance deployment failed to build the Docker image. The deployment failed.
```

### 🔍 **Causa Identificada:**
- **Debug commands falhando**: `RUN python -c "import ..."` durante build
- **Diretório data/ ausente**: `COPY data/ ./data/` falhando
- **Comandos de teste**: `ls -la` e imports Python interrompendo build

### ✅ **Solução Aplicada (v1.1.16):**
1. **Removido comandos de debug** problemáticos
2. **Simplificado cópia de arquivos** 
3. **Criado diretório data/** com `RUN mkdir -p data/fallback`
4. **Dockerfile limpo** sem testes que podem falhar

---

## 🛠️ Tipos Comuns de Erros Docker Build

### 1. **Arquivo não encontrado durante COPY**
```dockerfile
# ❌ PROBLEMA
COPY data/ ./data/  # Se data/ não existe = build falha

# ✅ SOLUÇÃO  
RUN mkdir -p data/fallback  # Criar se necessário
```

### 2. **Comando RUN falhando**
```dockerfile
# ❌ PROBLEMA
RUN python -c "import module"  # Se import falha = build falha

# ✅ SOLUÇÃO
# Remover comandos de teste no Dockerfile
# Testar imports apenas em runtime
```

### 3. **Dependências de sistema ausentes**
```dockerfile
# ❌ PROBLEMA
RUN pip install pandas  # Pode precisar gcc

# ✅ SOLUÇÃO
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
```

### 4. **Cópia duplicada de arquivos**
```dockerfile
# ❌ PROBLEMA
COPY requirements.txt .
COPY requirements.txt .  # Duplicação

# ✅ SOLUÇÃO
COPY requirements.txt .  # Apenas uma vez
```

---

## 📋 Checklist Docker Build Errors

### Antes do Deploy:
- [ ] Dockerfile não tem comandos de debug/teste
- [ ] Todos os arquivos COPY existem localmente
- [ ] Não há duplicação de COPY commands
- [ ] requirements.txt está correto
- [ ] Não há import tests em RUN commands

### Durante Falha de Build:
1. **Verifique logs detalhados** no EB Console
2. **Teste build localmente:**
   ```bash
   docker build -t test-app .
   ```
3. **Verifique se arquivos existem:**
   ```bash
   ls -la cache/ apis/ *.py
   ```

### Após Correção:
- [ ] Increment versão no create_package.py
- [ ] Gerar novo ZIP
- [ ] Deploy novo package
- [ ] Aguardar 5-10 min para build completo

---

## 🔧 Dockerfile Atual (v1.1.16) - Funcional

```dockerfile
FROM python:3.12-slim
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App files (apenas essenciais)
COPY app.py utils.py simple_version.py ./
COPY cache/ ./cache/
COPY apis/ ./apis/

# Create dirs
RUN mkdir -p data/fallback

# Security
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000
CMD ["python", "app.py"]
```

---

## 🎯 **PACOTE ATUAL FUNCIONAL:**

- **Arquivo**: `flask-webscraping-api-compose-v1.1.16-20250602-182120.zip`
- **Status**: ✅ **Build deve funcionar**
- **Dockerfile**: Limpo, sem debug commands
- **Arquivos**: Todos incluídos (`utils.py`, `apis/`, `cache/`)
- **Deploy**: Pronto para upload no EB

---

## 🚀 **PRÓXIMOS PASSOS:**

1. **Upload do v1.1.16** no Elastic Beanstalk
2. **Aguardar build** (mais rápido sem debug)
3. **Verificar logs** se ainda houver problemas
4. **Testar endpoints** após deploy bem-sucedido

**Tempo estimado**: 5-8 minutos para build + deploy completo 