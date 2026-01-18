# 🚀 TR4CTION AGENT V2 - PLANO DE DEPLOY EM PRODUÇÃO

**Versão:** 2.0  
**Data:** 14 de janeiro de 2026  
**Status:** Production Deployment Plan  
**Ambiente:** AWS EC2 (Ubuntu 22.04 LTS)

---

## ⚠️ CONTEXTO CRÍTICO

Este documento descreve o deploy **FINAL** em ambiente de **PRODUÇÃO REAL**. 

**NÃO é um experimento.** É responsabilidade de um engenheiro sênior.

### Restrições Absolutas
- ✋ NÃO ignorar erros
- ✋ NÃO "assumir que está ok"
- ✋ NÃO mascarar exceções
- ✋ NÃO seguir para o próximo passo sem validação clara

### Critério de Sucesso FINAL
Todos os itens abaixo devem ser **verdadeiros**:

- [ ] Backend FastAPI inicia **SEM ERRO**
- [ ] Frontend Next.js inicia **SEM ERRO**
- [ ] Alembic migrations aplicadas com sucesso
- [ ] Upload de template FCJ funciona em produção
- [ ] Snapshot e FillableDetector executam corretamente
- [ ] API acessível via IP público da EC2
- [ ] Nenhum erro no `journalctl` / logs
- [ ] Serviços sobem automaticamente após reboot

**Se QUALQUER item falhar** → ABORTAR deploy imediatamente e corrigir.

---

## 📋 CHECKLIST DE DEPLOY (11 PASSOS)

### PASSO 1: AUDITORIA INICIAL DO SERVIDOR

#### O que validar:
```bash
# 1.1 Versão do SO
$ lsb_release -a
# Esperado: Ubuntu 22.04 LTS

# 1.2 Espaço em disco
$ df -h /
# Esperado: > 20% livres

# 1.3 Usuário
$ whoami
# Não deve ser root (idealmente)

# 1.4 Python
$ python3 --version
# Esperado: Python 3.10+

# 1.5 Node.js
$ node --version && npm --version
# Esperado: v18+, npm 9+
```

#### Script automatizado (RECOMENDADO):
```bash
cd /path/to/Tr4ction_Agent_V2
bash scripts/deploy_audit.sh
```

#### Critério de Aprovação:
- [ ] Ubuntu 22.04 confirmado
- [ ] Espaço em disco > 20%
- [ ] Python 3.10+ instalado
- [ ] Node.js 18+ instalado
- [ ] Git disponível

---

### PASSO 2: ATIVAR E VALIDAR AMBIENTE PYTHON

#### Ativar venv:
```bash
cd /path/to/Tr4ction_Agent_V2
source venv/bin/activate
# ou
. venv/bin/activate
```

#### Atualizar pip:
```bash
pip install --upgrade pip setuptools wheel
```

#### Instalar dependências:
```bash
pip install -r backend/requirements.txt
```

**VERIFICAR SE NÃO HÁ ERRO** - se houver erro de pacote:
1. Anotar qual pacote falhou
2. Investigar versão incompatível
3. NÃO prosseguir até estar resolvido

#### Validar imports críticos:
```bash
python3 -c "
import fastapi
import sqlalchemy
import openpyxl
import alembic
import chromadb
print('✓ Todos os imports críticos OK')
"
```

#### Critério de Aprovação:
- [ ] venv ativado
- [ ] pip install sem erros
- [ ] Imports críticos OK

---

### PASSO 3: CORRIGIR IMPORT BLOQUEANTE (FOUNDATION CHECK)

#### Verificar founder.py:
```bash
grep -n "backend.enterprise" backend/routers/founder.py
```

**Se encontrar `backend.enterprise`:**

Este import **CAUSARÁ ERRO** no startup:
```
ModuleNotFoundError: No module named 'backend'
```

#### Opção 1: Verificar se módulo existe
```bash
ls -la backend/app/enterprise/
# Se não existir → corrigir import
```

#### Opção 2: Corrigir imports
Procurar por linhas tipo:
```python
from backend.app.services import ...
from backend.app.models import ...
```

E corrigir para:
```python
from app.services import ...
from app.models import ...
```

**VERIFICAR MUDANÇA:**
```bash
python3 -c "from routers import founder_router; print('✓ founder.py OK')"
```

#### Critério de Aprovação:
- [ ] Nenhum `from backend.` em routers/
- [ ] Import de founder.py funciona
- [ ] Nenhum ModuleNotFoundError

---

### PASSO 4: VALIDAÇÃO RIGOROSA DO .env

#### Arquivo crítico:
```
backend/.env
```

#### Variáveis OBRIGATÓRIAS:

```bash
# 4.1 Database
DATABASE_URL=sqlite:///data/tr4ction.db
# ou
DATABASE_URL=postgresql://user:pass@host/dbname

# 4.2 Storage de Templates
TEMPLATE_STORAGE_PATH=/abs/path/data/templates_storage
# Exemplo: /home/ubuntu/tr4ction/data/templates_storage

# 4.3 Diretório de dados
DATA_DIR=/abs/path/data
# Exemplo: /home/ubuntu/tr4ction/data

# 4.4 ChromaDB
CHROMA_PERSIST_DIR=/abs/path/data/chroma_db

# 4.5 JWT (SEGURO!)
JWT_SECRET=seu_secret_aleatorio_super_seguro_aqui
# Nunca usar "secret" ou "password"
# Gerar com: python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 4.6 LLM Provider
LLM_PROVIDER=groq  # ou openai

# Se groq:
GROQ_API_KEY=sua_chave_groq_aqui

# Se openai:
OPENAI_API_KEY=sua_chave_openai_aqui

# 4.7 CORS (Produção)
CORS_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com

# 4.8 Debug
DEBUG_MODE=false  # NUNCA true em produção
```

#### Script de validação:
```bash
python3 << 'EOF'
import os
from dotenv import load_dotenv

env_file = "backend/.env"
load_dotenv(env_file)

critical_vars = [
    "DATABASE_URL",
    "TEMPLATE_STORAGE_PATH",
    "DATA_DIR",
    "CHROMA_PERSIST_DIR",
    "JWT_SECRET",
    "LLM_PROVIDER",
    "DEBUG_MODE"
]

print("Validando .env...")
for var in critical_vars:
    value = os.getenv(var)
    if not value:
        print(f"✗ {var} está vazio!")
        exit(1)
    print(f"✓ {var}")

llm = os.getenv("LLM_PROVIDER")
if llm == "groq" and not os.getenv("GROQ_API_KEY"):
    print("✗ LLM_PROVIDER=groq mas GROQ_API_KEY não definida!")
    exit(1)

if llm == "openai" and not os.getenv("OPENAI_API_KEY"):
    print("✗ LLM_PROVIDER=openai mas OPENAI_API_KEY não definida!")
    exit(1)

print("\n✓ Todas as variáveis .env validadas!")
EOF
```

#### Critério de Aprovação:
- [ ] Todas as variáveis críticas definidas
- [ ] Nenhuma variável vazia
- [ ] LLM_PROVIDER e chave correspondente OK
- [ ] DEBUG_MODE=false
- [ ] JWT_SECRET é forte

---

### PASSO 5: ALEMBIC (BANCO DE DADOS É O SISTEMA)

#### Executar migrations:
```bash
cd backend
alembic upgrade head
```

**Output esperado:**
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_fcj_templates...
```

#### Verificar se tabelas foram criadas:
```bash
python3 << 'EOF'
import sqlite3

conn = sqlite3.connect("data/tr4ction.db")
cursor = conn.cursor()

# Verificar tabelas FCJ
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('template_definitions', 'fillable_fields')")
tables = cursor.fetchall()

if len(tables) == 2:
    print("✓ Tabelas FCJ criadas com sucesso")
    
    # Mostrar schema
    for table_name in ['template_definitions', 'fillable_fields']:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"\nTabela: {table_name}")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
else:
    print(f"✗ Faltam tabelas. Encontradas: {tables}")
    exit(1)

conn.close()
EOF
```

**Se falhar:**
1. Verificar se alembic.ini existe
2. Verificar DATABASE_URL em .env
3. Rodar novamente: `alembic upgrade head`

#### Critério de Aprovação:
- [ ] `alembic upgrade head` executado sem erro
- [ ] Tabelas `template_definitions` e `fillable_fields` existem
- [ ] Schema das tabelas está correto

---

### PASSO 6: STORAGE E PERMISSÕES

#### Criar diretórios:
```bash
# Extrair paths do .env
source backend/.env

# Criar estrutura
mkdir -p $TEMPLATE_STORAGE_PATH
mkdir -p $DATA_DIR/chroma_db
mkdir -p $DATA_DIR/templates_images
mkdir -p $DATA_DIR/knowledge
mkdir -p $DATA_DIR/uploads

# Validar
ls -la $DATA_DIR
ls -la $TEMPLATE_STORAGE_PATH
```

#### Verificar permissões:
```bash
# Usuário atual deve ter permissão de escrita
touch $DATA_DIR/test_write.txt && rm $DATA_DIR/test_write.txt
echo "✓ Permissão de escrita OK"
```

**Se falhar:**
```bash
# Dar permissões
chmod 755 $DATA_DIR
chmod 755 $TEMPLATE_STORAGE_PATH
```

#### Critério de Aprovação:
- [ ] Todos os diretórios existem
- [ ] Usuário tem permissão de escrita
- [ ] Nenhum path relativo

---

### PASSO 7: STARTUP CONTROLADO DO BACKEND

#### Teste 1: Import do módulo
```bash
cd backend
python3 -c "from main import app; print('✓ Backend importado com sucesso')"
```

**Se falhar:**
```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    from main import app
  File ".../backend/main.py", line XX, in <module>
    ModuleNotFoundError: No module named '...'
```

**Ação:** Voltar ao PASSO 3 e corrigir imports.

#### Teste 2: Startup com uvicorn
```bash
cd backend
timeout 5 uvicorn main:app --host 0.0.0.0 --port 8000 &
sleep 2

# Testar health check
curl -s http://localhost:8000/health | python3 -m json.tool

# Resultado esperado:
# {
#   "status": "ok",
#   "version": "2.0.0"
# }

# Parar servidor
pkill -f "uvicorn main:app"
```

**Se health check falhar:**
```bash
# Ver logs completos
uvicorn main:app --host 0.0.0.0 --port 8000
# Ctrl+C para parar
```

#### Critério de Aprovação:
- [ ] Import do main.py sem erro
- [ ] uvicorn inicia
- [ ] Health endpoint responde com 200 OK
- [ ] Nenhum traceback nos logs

---

### PASSO 8: TESTE REAL DO PIPELINE FCJ EM PRODUÇÃO

#### Preparar arquivo de teste:
```bash
# Criar arquivo Excel simples para testar
python3 << 'EOF'
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

wb = Workbook()
ws = wb.active
ws.title = "ICP"

# Titulo
ws['A1'] = "Template FCJ - Teste"
ws['A1'].font = Font(bold=True, size=14, color="FFFFFF")
ws['A1'].fill = PatternFill(start_color="0070C0", end_color="0070C0", fill_type="solid")

# Campo preenchível
ws['B3'] = "Nome da Empresa"  # Label
ws['B4'] = ""  # Campo vazio para preencher
ws['B4'].fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

# Salvar
wb.save("test_template.xlsx")
print("✓ test_template.xlsx criado")
EOF
```

#### Iniciar backend em background:
```bash
cd backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
sleep 3
```

#### Fazer upload e testar:
```bash
# Obter token (substitui TOKEN)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' \
  | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['access_token'])"

# Ou usar token hardcoded se disponível
TOKEN="seu_token_aqui"

# Upload do template
curl -X POST "http://localhost:8000/admin/templates/upload?cycle=Q1_TEST" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_template.xlsx" \
  | python3 -m json.tool
```

**Response esperada:**
```json
{
  "template_id": 1,
  "template_key": "q1_test_template",
  "cycle": "Q1_TEST",
  "file_hash_sha256": "abc123...",
  "stats": {
    "num_sheets": 1,
    "num_cells": 100,
    "num_fields": 1
  },
  "validation_report": {
    "valid": true,
    "errors": []
  },
  "fields_count": 1
}
```

#### Validações obrigatórias:
```bash
# Verificar log do backend
tail -50 backend.log

# Status code 200
# Sem erros de snapshot
# Sem erros de detector
# fields_count > 0
```

#### Critério de Aprovação:
- [ ] Backend inicia
- [ ] Endpoint /admin/templates/upload acessível
- [ ] Upload do arquivo funciona
- [ ] Response status 200
- [ ] validation_report.valid == true
- [ ] fields_count > 0
- [ ] Nenhum erro nos logs

---

### PASSO 9: FRONTEND (NEXT.JS)

#### Configurar .env.local:
```bash
cd frontend

# Criar arquivo
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://IP_PUBLICA_EC2:8000
NEXT_PUBLIC_APP_NAME=TR4CTION Agent
EOF

# Exemplo:
# NEXT_PUBLIC_API_URL=http://54.123.45.67:8000
```

#### Instalar dependências:
```bash
npm install
```

**Se houver erro de peer dependency:**
```bash
npm install --legacy-peer-deps
```

#### Build:
```bash
npm run build
```

**Esperado:**
```
✓ Compiled successfully
```

#### Iniciar frontend:
```bash
npm run start
# ou com PM2 (recomendado para produção)
npm install -g pm2
pm2 start "npm start" --name "tr4ction-frontend"
pm2 save
```

#### Testar acesso:
```bash
# Abrir em browser ou curl
curl http://localhost:3000
# Esperado: HTML da página

# Ou verificar se porta 3000 está ouvindo
netstat -tlnp | grep 3000
```

#### Critério de Aprovação:
- [ ] npm install sem erros
- [ ] npm run build sucesso
- [ ] Frontend inicia na porta 3000
- [ ] Acesso via http://IP:3000

---

### PASSO 10: SUPERVISÃO (PRODUÇÃO DE VERDADE)

#### Opção A: systemd (RECOMENDADO)

Criar arquivo de serviço para backend:
```bash
sudo tee /etc/systemd/system/tr4ction-backend.service > /dev/null << 'EOF'
[Unit]
Description=TR4CTION Agent Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Tr4ction_Agent_V2/backend
Environment="PATH=/home/ubuntu/Tr4ction_Agent_V2/venv/bin"
ExecStart=/home/ubuntu/Tr4ction_Agent_V2/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Criar arquivo para frontend:
```bash
sudo tee /etc/systemd/system/tr4ction-frontend.service > /dev/null << 'EOF'
[Unit]
Description=TR4CTION Agent Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Tr4ction_Agent_V2/frontend
Environment="PATH=/home/ubuntu/Tr4ction_Agent_V2/venv/bin:/usr/local/bin"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Habilitar e iniciar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable tr4ction-backend.service
sudo systemctl enable tr4ction-frontend.service
sudo systemctl start tr4ction-backend.service
sudo systemctl start tr4ction-frontend.service

# Verificar status
sudo systemctl status tr4ction-backend.service
sudo systemctl status tr4ction-frontend.service
```

#### Opção B: PM2 (Alternativa)

```bash
pm2 start /home/ubuntu/Tr4ction_Agent_V2/backend/main.py --name "backend" --interpreter python
pm2 start "npm start" --cwd /home/ubuntu/Tr4ction_Agent_V2/frontend --name "frontend"
pm2 save
pm2 startup
```

#### Critério de Aprovação:
- [ ] Backend service criado e rodando
- [ ] Frontend service criado e rodando
- [ ] Ambos com restart automático
- [ ] Status: active (running)

---

### PASSO 11: VERIFICAÇÃO FINAL (GO / NO-GO)

#### Checklist FINAL:

```
BACKEND
-------
[ ] python backend/main.py inicia sem erro
[ ] uvicorn inicia na porta 8000
[ ] Health check (/health) responde
[ ] POST /admin/templates/upload funciona
[ ] Snapshot gerado corretamente
[ ] Fields detectados (> 0)
[ ] Nenhum erro no journalctl

FRONTEND
--------
[ ] npm install sucesso
[ ] npm run build sucesso
[ ] npm start inicia na porta 3000
[ ] Página acessível em http://IP:3000
[ ] Conecta ao backend (sem CORS error)

DATABASE
--------
[ ] alembic upgrade head OK
[ ] Tabelas template_definitions OK
[ ] Tabelas fillable_fields OK
[ ] Dados persistem após reboot

SUPERVISÃO
----------
[ ] Serviços em systemd/PM2
[ ] Restart automático configurado
[ ] Logs acessíveis
[ ] Reboot da EC2 → serviços sobem sozinhos

SEGURANÇA
---------
[ ] DEBUG_MODE=false
[ ] JWT_SECRET é forte
[ ] CORS_ORIGINS configurado
[ ] NÃO há credenciais em logs
```

#### Script de validação final:

```bash
#!/bin/bash
echo "Iniciando validação final..."

# Backend
echo -n "Backend: "
curl -s http://localhost:8000/health > /dev/null && echo "✓" || echo "✗"

# Frontend
echo -n "Frontend: "
curl -s http://localhost:3000 | grep -q "DOCTYPE" && echo "✓" || echo "✗"

# Database
echo -n "Database: "
python3 -c "
import sqlite3
conn = sqlite3.connect('backend/data/tr4ction.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM template_definitions')
count = cursor.fetchone()[0]
print(f'✓ ({count} templates)')
" || echo "✗"

echo ""
echo "Se todos forem ✓: DEPLOY APROVADO"
```

---

## 🔄 ROLLBACK (Se algo der errado)

#### Rollback de database:
```bash
cd backend
alembic downgrade -1  # Volta 1 migration
# ou
alembic downgrade base  # Volta ao estado inicial
```

#### Rollback de código:
```bash
git revert HEAD~1  # Volta último commit
# ou
git checkout <commit_hash>  # Volta para commit específico
```

#### Parar serviços:
```bash
sudo systemctl stop tr4ction-backend.service
sudo systemctl stop tr4ction-frontend.service
```

---

## 📊 MÉTRICAS PÓS-DEPLOY

Monitorar por 24-48 horas:

```
[ ] Taxa de erro < 0.1%
[ ] Tempo de resposta P95 < 1000ms
[ ] CPU usage < 70%
[ ] Memory usage < 80%
[ ] Disk usage < 80%
[ ] Nenhum traceback em logs
[ ] Nenhum silent failure
```

---

## 📞 SUPORTE

Se encontrar erro durante o deploy:

1. **Anotar exatamente qual passo falhou**
2. **Copiar o erro completo (traceback)**
3. **Desativar DEBUG_MODE para investigar**
4. **NÃO ignorar warnings**
5. **Consultar logs**: `journalctl -u tr4ction-backend.service -n 100`

---

**Status:** 🟢 Pronto para Deploy  
**Responsável:** Engenheiro de Produção  
**Data de Criação:** 2026-01-14
