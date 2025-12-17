# 🚀 Guia de Deploy - TR4CTION Agent no Vercel

## Pré-requisitos

1. ✅ Conta no GitHub (código do frontend lá)
2. ✅ Conta no Vercel (gratuito)
3. ✅ Backend rodando em servidor acessível (EC2, Railway, Render, etc)

## Passo 1: Preparar o Repositório GitHub

```bash
cd c:\Users\Micro\Desktop\Tr4ction_Agent_V2

# Inicializar Git (se não existir)
git init

# Adicionar remote
git remote add origin https://github.com/SEU_USER/tr4ction-agent.git

# Fazer commit
git add .
git commit -m "Initial commit - TR4CTION Agent"

# Push para GitHub
git push -u origin main
```

## Passo 2: Configurar Backend para Produção

O backend precisa estar acessível publicamente. Opções:

### Opção A: AWS EC2 (Atual - 54.144.92.71)
- Backend já está lá
- Use URL: `https://54.144.92.71.sslip.io`
- Configure CORS no `.env` do backend:
  ```
  CORS_ORIGINS=https://tr4ction-v2-agent.vercel.app,https://www.tr4ction-v2-agent.vercel.app,https://54.144.92.71.sslip.io
  ```

### Opção B: Railway/Render/Fly.io
- Deploy fácil do backend Python
- Cria domínio automático: `https://seu-backend.railway.app`

## Passo 3: Deploy no Vercel

### Via CLI (Recomendado)

1. Instalar Vercel CLI:
```bash
npm install -g vercel
```

2. Login:
```bash
vercel login
```

3. Deploy (do diretório frontend):
```bash
cd frontend
vercel
```

4. Seguir as instruções interativas

### Via Dashboard Vercel

1. Acessar: https://vercel.com/dashboard
2. Clicar em "Add New..." → "Project"
3. Importar repositório GitHub
4. Configurações:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

## Passo 4: Configurar Variáveis de Ambiente

**No Dashboard Vercel:**

1. Settings → Environment Variables
2. Adicionar:
   ```
   NEXT_PUBLIC_API_BASE_URL=https://seu-backend.com
   NEXT_PUBLIC_USE_LIVE_API=true
   ```

## Passo 5: Deploy Automático

Configure GitHub integration para auto-deploy:

1. Dashboard → Settings → Git
2. Production Branch: `main`
3. Qualquer push em `main` faz deploy automático

## ✅ Verificar o Deploy

1. Acesse sua URL do Vercel
2. Teste o login com credenciais admin
3. Verifique no console do navegador se há erros CORS
4. Teste chat functionality

## 🔧 Troubleshooting

### Erro CORS
- Backend não tem Vercel URL nas CORS_ORIGINS
- Adicione em `.env` do backend:
  ```
  CORS_ORIGINS=...seu-vercel-url.vercel.app
  ```

### Erro de Conexão ao Backend
- Backend não está rodando
- URL do backend está errada
- Firewall bloqueando
- Verificar variável `NEXT_PUBLIC_API_BASE_URL`

### Build falha no Vercel
- Executar `npm run build` localmente para testar
- Verificar Node version (deve ser 18+)
- Limpar dependências: `npm ci` vs `npm install`

## 📊 Status Atual

- ✅ Frontend pronto para Vercel
- ✅ Backend preparado
- ⏳ Aguardando GitHub repo
- ⏳ Aguardando conexão Vercel

## 🎯 Próximos Passos

1. Fazer commit do código no GitHub
2. Conectar Vercel ao repositório
3. Configurar variáveis de ambiente
4. Disparar deploy
5. Validar em produção

**Precisa de ajuda com algum passo? Avise!**
