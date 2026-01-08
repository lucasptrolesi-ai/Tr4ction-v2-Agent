# 🔧 TR4CTION Frontend - Configuração de API

## ✅ Problema Resolvido

Todas as chamadas HTTP do frontend agora usam variáveis de ambiente para apontar corretamente para o backend, independente do domínio onde o frontend está hospedado (Vercel, localhost, etc).

## 📋 Arquivos Modificados

### 1. `/frontend/app/test-login/page.jsx`
**Antes:**
```javascript
const response = await fetch('http://127.0.0.1:8000/auth/login', {
```

**Depois:**
```javascript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
const response = await fetch(`${API_BASE}/auth/login`, {
```

### 2. `/frontend/.env.local` (atualizado)
Adicionadas todas as variáveis de API para compatibilidade:
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

### 3. `/frontend/.env.example` (criado)
Template com documentação das variáveis.

## 🎯 Arquivos Já Corretos

Os seguintes arquivos já estavam usando o padrão correto:

- ✅ `/frontend/lib/api.js` - Client centralizado com `API_BASE`
- ✅ `/frontend/lib/auth.js` - Autenticação usando `API_BASE`
- ✅ `/frontend/app/admin/knowledge/page.jsx` - Usa `backendBase`
- ✅ `/frontend/app/admin/page.jsx` - Usa `backendBase`
- ✅ `/frontend/app/admin/dashboard/page.jsx` - Usa `apiGet`, `apiPost`
- ✅ `/frontend/app/founder/dashboard/page.jsx` - Usa `apiGet`
- ✅ `/frontend/app/founder/templates/page.jsx` - Usa `apiGet`, `apiDownload`

## 🚀 Como Usar

### Desenvolvimento Local
```bash
cd frontend
cp .env.example .env.local
# Editar .env.local se necessário
npm run dev
```

### Produção (Vercel)
Configurar as variáveis de ambiente no dashboard do Vercel:

```
NEXT_PUBLIC_API_URL=https://api.tr4ction.ai
NEXT_PUBLIC_API_BASE_URL=https://api.tr4ction.ai
NEXT_PUBLIC_BACKEND_URL=https://api.tr4ction.ai
```

## 📚 Padrões de Uso

### Opção 1: Usar Client Centralizado (Recomendado)
```javascript
import { apiGet, apiPost, apiPut, apiDownload } from '@/lib/api';

// GET
const data = await apiGet('/admin/users');

// POST
const result = await apiPost('/admin/trails', { name: 'Nova Trilha' });

// Download
await apiDownload('/founder/trails/123/export/xlsx', 'export.xlsx');
```

### Opção 2: Usar Variável de Ambiente Diretamente
```javascript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 
                 process.env.NEXT_PUBLIC_API_BASE_URL || 
                 'http://127.0.0.1:8000';

const response = await fetch(`${API_BASE}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password }),
});
```

### Opção 3: Para Componentes com Axios
```javascript
const backendBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

const res = await axios.get(`${backendBase}/admin/knowledge`);
```

## ⚠️ Importante

1. **NUNCA** hardcode URLs como:
   - ❌ `fetch('http://127.0.0.1:8000/...')`
   - ❌ `axios.get('/admin/users')` (caminho relativo)
   - ❌ `fetch('/auth/login')` (caminho relativo)

2. **SEMPRE** use uma das opções acima com variáveis de ambiente.

3. **Não commite** `.env.local` no git (já está no `.gitignore` da raiz do projeto).

## 🔍 Verificação

Para verificar se tudo está correto:

```bash
# No diretório frontend
grep -r "fetch\('" app/ | grep -v "API_BASE\|backendBase\|apiGet\|apiPost"
grep -r 'axios\.' app/ | grep -E '(get|post|put|delete)\(['"](/|`)' 
```

Se não retornar resultados, está tudo ok! ✅

## 📞 Variáveis de Ambiente Disponíveis

O frontend aceita 3 nomes diferentes para compatibilidade:

1. `NEXT_PUBLIC_API_URL` (preferido)
2. `NEXT_PUBLIC_API_BASE_URL` (compatibilidade)
3. `NEXT_PUBLIC_BACKEND_URL` (legacy em alguns componentes)

**Recomendação:** Configure todas as 3 com o mesmo valor para máxima compatibilidade.

---

**Status:** ✅ Todas as chamadas HTTP agora apontam corretamente para o backend!
