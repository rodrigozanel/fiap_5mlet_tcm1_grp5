# Guia da Collection Postman - API Flask Dados Vitivinícolas

Este guia explica como importar e usar a collection do Postman para testar a API Flask de Web Scraping.

## 📥 Como Importar a Collection

### Método 1: Importar arquivo JSON
1. Abra o Postman
2. Clique em **"Import"** (canto superior esquerdo)
3. Selecione **"Upload Files"**
4. Escolha o arquivo `postman_collection.json`
5. Clique em **"Import"**

### Método 2: Importar via URL (se hospedado)
1. Abra o Postman
2. Clique em **"Import"**
3. Selecione **"Link"**
4. Cole a URL do arquivo JSON
5. Clique em **"Continue"** e depois **"Import"**

## 🔧 Configuração Inicial

### 1. Verificar Variáveis de Ambiente
A collection já vem com variáveis pré-configuradas:
- `base_url`: `http://localhost:5000`
- `username`: `user1`
- `password`: `password1`

### 2. Modificar Variáveis (se necessário)
1. Clique na collection **"API Flask - Dados Vitivinícolas Embrapa"**
2. Vá para a aba **"Variables"**
3. Modifique os valores conforme necessário:
   - Para usar em produção, altere `base_url`
   - Para testar com user2, altere `username` e `password`

## 🚀 Como Usar a Collection

### 📁 Estrutura da Collection

A collection está organizada em 6 pastas principais:

#### 1. **Produção** 🍇
- Dados de Produção - Todos os Anos
- Dados de Produção - Filtrado por Ano
- Dados de Produção - Com Sub-opção

#### 2. **Processamento** ⚙️
- Dados de Processamento - Todos os Anos
- Dados de Processamento - Filtrado por Ano

#### 3. **Comercialização** 🛒
- Dados de Comercialização - Todos os Anos
- Dados de Comercialização - Filtrado por Ano

#### 4. **Importação** 📦
- Dados de Importação - Todos os Anos
- Dados de Importação - Filtrado por Ano

#### 5. **Exportação** 🚢
- Dados de Exportação - Todos os Anos
- Dados de Exportação - Filtrado por Ano

#### 6. **Testes de Autenticação** 🔐
- Teste sem Autenticação (Deve falhar)
- Teste com Credenciais Inválidas (Deve falhar)
- Teste com User2 (Deve funcionar)

### 🎯 Executando Requisições

#### Requisição Individual:
1. Selecione uma requisição
2. Clique em **"Send"**
3. Veja a resposta na parte inferior

#### Executar Pasta Completa:
1. Clique com botão direito em uma pasta
2. Selecione **"Run folder"**
3. Configure as opções de execução
4. Clique em **"Run"**

#### Executar Collection Completa:
1. Clique com botão direito na collection
2. Selecione **"Run collection"**
3. Configure as opções
4. Clique em **"Run"**

## 🧪 Testes Automáticos

A collection inclui testes automáticos que verificam:

### ✅ Testes Gerais (todas as requisições):
- Resposta não está vazia
- Tempo de resposta aceitável (< 30 segundos)

### ✅ Testes para Requisições Autenticadas (status 200):
- Estrutura correta da resposta JSON
- Presença dos campos obrigatórios: `data`, `header`, `body`, `footer`

### ✅ Testes para Autenticação Inválida:
- Retorna status 401 para requisições não autenticadas

### 📊 Visualizando Resultados dos Testes:
1. Após executar uma requisição, vá para a aba **"Test Results"**
2. Veja quais testes passaram (✅) ou falharam (❌)
3. Para execução em lote, veja o relatório completo no Collection Runner

## 🔧 Personalizando Requisições

### Modificar Parâmetros:
1. Selecione uma requisição
2. Vá para a aba **"Params"**
3. Modifique os valores de `year` ou `sub_option`
4. Clique em **"Send"**

### Testar Diferentes Anos:
- 2023, 2022, 2021, etc.
- Deixe vazio para todos os anos

### Testar Sub-opções:
- `vinhos`, `sucos`, `derivados`, etc.
- Deixe vazio para todas as opções

## 🔐 Testando Autenticação

### Credenciais Disponíveis:
- **Usuário 1**: `user1` / `password1`
- **Usuário 2**: `user2` / `password2`

### Para Testar Diferentes Usuários:
1. Vá para a aba **"Authorization"** da requisição
2. Modifique username e password
3. Ou altere as variáveis da collection

## 📈 Monitoramento e Debugging

### Console do Postman:
1. Abra **View > Show Postman Console**
2. Veja logs detalhados das requisições
3. Útil para debugging

### Salvando Respostas:
1. Após uma requisição bem-sucedida
2. Clique em **"Save Response"**
3. Escolha **"Save as example"**
4. Útil para documentação

## 🚨 Solução de Problemas

### Erro de Conexão:
- ✅ Verifique se a API está rodando (`python app.py`)
- ✅ Confirme se a URL está correta (`http://localhost:5000`)
- ✅ Verifique se não há firewall bloqueando

### Erro 401 (Não Autorizado):
- ✅ Verifique as credenciais na aba **"Authorization"**
- ✅ Confirme se está usando `user1/password1` ou `user2/password2`

### Erro 404 (Não Encontrado):
- ✅ Verifique se o endpoint está correto
- ✅ Confirme se a API está rodando

### Timeout:
- ✅ Aumente o timeout nas configurações do Postman
- ✅ Verifique a conexão com a internet (para web scraping)

## 💡 Dicas Avançadas

### 1. Usar Ambientes:
- Crie ambientes separados para desenvolvimento e produção
- Configure diferentes `base_url` para cada ambiente

### 2. Automatizar Testes:
- Use o Collection Runner para testes automatizados
- Configure execução periódica com Postman Monitors

### 3. Exportar Resultados:
- Exporte resultados dos testes em JSON ou HTML
- Útil para relatórios e documentação

### 4. Compartilhar Collection:
- Publique a collection no Postman para compartilhar com a equipe
- Use workspaces colaborativos

## 📞 Suporte

Se encontrar problemas:
1. Verifique se a API está rodando
2. Consulte os logs da aplicação Flask
3. Use o Console do Postman para debugging
4. Verifique a documentação Swagger em `http://localhost:5000/apidocs/`

---

**🎉 Agora você está pronto para testar a API Flask com o Postman!** 