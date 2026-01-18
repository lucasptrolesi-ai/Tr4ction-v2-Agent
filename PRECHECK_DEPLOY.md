# ✅ CHECKLIST PRÉ-DEPLOY - VALIDAÇÃO LOCAL

**Antes de fazer deploy em AWS, validar TUDO localmente em primeiro.**

**Versão:** 2.0  
**Data:** 14 de janeiro de 2026

---

## 🔴 VERIFICAÇÕES CRÍTICAS (DEVE PASSAR 100%)

### 1. Backend - Import Validation
```bash
cd backend
python3 -c "from main import app; print('✓ Backend imports OK')"
```
**Esperado:** `✓ Backend imports OK`  
**Se falhar:** Corrigir imports em `backend/routers/*.py`

---

### 2. Database - Table Creation
```bash
cd backend
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect("data/tr4ction.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = {row[0] for row in cursor.fetchall()}

required = {'template_definitions', 'fillable_fields'}
if required.issubset(tables):
    print("✓ Tabelas FCJ existem")
else:
    print(f"✗ Faltam: {required - tables}")
    exit(1)
conn.close()
EOF
```
**Esperado:** `✓ Tabelas FCJ existem`  
**Se falhar:** Rodar `alembic upgrade head`

---

### 3. Storage Paths - Exist & Writable
```bash
source backend/.env
test -d "$TEMPLATE_STORAGE_PATH" && echo "✓ TEMPLATE_STORAGE_PATH existe" || echo "✗ TEMPLATE_STORAGE_PATH não existe"
test -w "$TEMPLATE_STORAGE_PATH" && echo "✓ Escrita OK" || echo "✗ Sem permissão"
```
**Esperado:** Ambas ✓  
**Se falhar:** `mkdir -p $TEMPLATE_STORAGE_PATH && chmod 755 $TEMPLATE_STORAGE_PATH`

---

### 4. Env Variables - No Blank Values
```bash
source backend/.env

for var in DATABASE_URL TEMPLATE_STORAGE_PATH DATA_DIR JWT_SECRET LLM_PROVIDER DEBUG_MODE; do
    val=$(eval echo \$$var)
    if [ -z "$val" ]; then
        echo "✗ $var está vazio"
        exit 1
    else
        echo "✓ $var = ${val:0:20}..."
    fi
done
```
**Esperado:** Todas ✓  
**Se falhar:** Editar `backend/.env` e preencher valores

---

### 5. Backend Startup - Health Check
```bash
cd backend
timeout 5 python3 -c "
from main import app
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.get('/health')
assert response.status_code == 200, f'Status {response.status_code}'
print('✓ Health endpoint OK')
" || exit 1
```
**Esperado:** `✓ Health endpoint OK`  
**Se falhar:** Verificar logs: `python3 main.py`

---

### 6. Template Upload - Integration Test
```bash
cd backend

# Criar arquivo de teste
python3 << 'SETUP'
from openpyxl import Workbook
wb = Workbook()
ws = wb.active
ws.title = "ICP"
ws['A1'] = "Teste"
ws['B1'] = ""
wb.save("/tmp/test_template.xlsx")
print("✓ test_template.xlsx criado")
SETUP

# Testar upload (requer token válido)
# Alternativa: rodar pytest
pytest app/tests/test_admin_upload_pipeline.py -v
```
**Esperado:** Testes passam  
**Se falhar:** Verificar erro específico no test

---

### 7. No Blocking Imports
```bash
grep -r "from backend\." backend/routers/ 2>/dev/null || echo "✓ Nenhum 'from backend.' encontrado"
grep -r "backend.enterprise" backend/ 2>/dev/null || echo "✓ Nenhum 'backend.enterprise' encontrado"
```
**Esperado:** Ambos ✓  
**Se falhar:** Corrigir imports

---

### 8. Alembic Configuration
```bash
cd backend
test -f "alembic.ini" && echo "✓ alembic.ini existe" || echo "✗ alembic.ini faltando"
test -f "app/db/migrations/env.py" && echo "✓ env.py existe" || echo "✗ env.py faltando"
alembic current || echo "✗ Alembic não funciona"
```
**Esperado:** Todas ✓  
**Se falhar:** Recriar arquivos ou rodar `alembic init`

---

### 9. Frontend Dependencies
```bash
cd frontend
npm list 2>&1 | head -5
# Procurar por "npm ERR!"

if npm list 2>&1 | grep -q "npm ERR!"; then
    echo "✗ Dependências com erro"
    exit 1
else
    echo "✓ Dependências OK"
fi
```
**Esperado:** `✓ Dependências OK`  
**Se falhar:** `npm install --legacy-peer-deps`

---

### 10. Frontend Build
```bash
cd frontend
npm run build
# Verificar se "✓ Compiled successfully"
```
**Esperado:** Sucesso sem erros  
**Se falhar:** Verificar erro em stdout

---

## 🟡 VERIFICAÇÕES RECOMENDADAS

### Espaço em Disco
```bash
df -h / | awk 'NR==2 {print $5}'
# Esperado: < 80%
```

### Python Version
```bash
python3 --version
# Esperado: Python 3.10+
```

### Node Version
```bash
node -v
# Esperado: v18+
```

### Git Status
```bash
git status
# Esperado: "working tree clean"
```

### Log Files Checked
```bash
# Nenhum erro em:
grep -i "error\|fatal\|critical" backend/backend.log 2>/dev/null
grep -i "error\|fatal\|critical" frontend/npm.log 2>/dev/null
```

---

## 🔵 VALIDAÇÃO SEMI-AUTOMÁTICA

Executar script de validação:
```bash
python3 scripts/validate_production.py
```

**Esperado:** Resultado `GO/DEPLOY APROVADO`

Se `NO-GO/DEPLOY REJEITADO`:
- Anotar qual teste falhou
- Corrigir o erro específico
- Rodar script novamente

---

## 📊 RESULTADO FINAL

Se TODOS os testes ✓ passarem:

```
✓ Backend - Import OK
✓ Database - Tabelas criadas
✓ Storage - Paths válidos
✓ Env - Todas as variáveis
✓ Health - Endpoint responde
✓ Upload - Pipeline funciona
✓ Imports - Sem bloqueios
✓ Alembic - Configurado
✓ Frontend - Dependencies OK
✓ Frontend - Build OK

===========================================
RESULTADO: GO / DEPLOY APROVADO
===========================================

Próximo passo: Deploy em AWS EC2
```

---

## 🛑 SE ALGUM TESTE FALHAR

**NÃO fazer deploy até corrigir.** Investigar:

```bash
# 1. Ler mensagem de erro completamente
# 2. Procurar em logs:
cat backend/backend.log | tail -50
grep "ERROR\|CRITICAL" frontend/npm.log

# 3. Reverter última mudança se foi recente
git log --oneline -5
git diff HEAD~1

# 4. Testar componente isolado
pytest app/tests/test_snapshot_completeness.py -v -s

# 5. Se persistir, pedir ajuda com:
#    - Output completo do erro
#    - Stack trace
#    - Ambiente (Python version, Node version, etc)
```

---

**Checklist completo?** ✅ Pronto para produção!
