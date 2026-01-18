# 🚀 DEPLOY PRODUCTION - GUIA RÁPIDO DE REFERÊNCIA

**Para SRE / Engenheiro de Produção**  
**Versão:** 2.0  
**Data:** 14 de janeiro de 2026

---

## ⚡ TL;DR (O que fazer em 30 segundos)

```bash
# 1. SSH na EC2
ssh -i key.pem ubuntu@IP_PUBLICA

# 2. Clone/atualizar código
cd Tr4ction_Agent_V2
git pull origin main

# 3. Rodar validação automática
bash scripts/deploy_audit.sh

# 4. Se ✓, rodar testes de produção
python3 scripts/validate_production.py

# 5. Se ✓, iniciar serviços
sudo systemctl start tr4ction-backend.service
sudo systemctl start tr4ction-frontend.service

# 6. Verificar
curl http://localhost:8000/health
curl http://localhost:3000
```

**Se algo falhar em qualquer etapa:** ABORTAR e corrigir.

---

## 📋 CHECKLIST CRÍTICO

### Antes do Deploy
- [ ] Código atual em main branch do GitHub
- [ ] .env em backend/ com todas as variáveis (verificar `cat backend/.env | grep -c "="`)
- [ ] Database sqlite em backend/data/ ou PostgreSQL configurado
- [ ] AWS EC2 com Ubuntu 22.04, Python 3.10+, Node.js 18+
- [ ] Espaço em disco > 20GB
- [ ] Permissões corretas para usuário ubuntu

### Durante o Deploy
- [ ] `bash scripts/deploy_audit.sh` → sem erros
- [ ] `python3 scripts/validate_production.py` → GO aprovado
- [ ] Health check: `curl http://localhost:8000/health` → 200 OK
- [ ] Nenhum ModuleNotFoundError nos logs
- [ ] Nenhum erro de database
- [ ] Nenhum erro de armazenamento

### Depois do Deploy
- [ ] systemd services rodando: `sudo systemctl status tr4ction-backend`
- [ ] Frontend acessível: `curl http://localhost:3000`
- [ ] Upload FCJ funciona: testa POST /admin/templates/upload
- [ ] Reboot da EC2 → serviços sobem automaticamente

---

## 🔧 PASSOS PRINCIPAIS

### PASSO 1: Preparar Servidor

```bash
# Versão do SO
lsb_release -a
# Esperado: Ubuntu 22.04 LTS

# Espaço em disco
df -h /
# Esperado: > 20% livres

# Python
python3 --version
# Esperado: Python 3.10+

# Node.js
node -v && npm -v
# Esperado: v18+, npm 9+
```

### PASSO 2: Clonar/Atualizar Código

```bash
cd /home/ubuntu
git clone https://github.com/seu-org/Tr4ction_Agent_V2.git
cd Tr4ction_Agent_V2
git pull origin main  # Se já existe
```

### PASSO 3: Setup do Ambiente Python

```bash
# Criar venv (se não existir)
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt

# Validar
python3 -c "import fastapi, sqlalchemy, openpyxl; print('✓ OK')"
```

### PASSO 4: Configurar .env

```bash
cd backend

# Editar .env (usar nano, vim, etc)
nano .env

# Validar que contém (sem valores vazios):
# - DATABASE_URL
# - TEMPLATE_STORAGE_PATH
# - DATA_DIR
# - JWT_SECRET
# - LLM_PROVIDER
# - GROQ_API_KEY ou OPENAI_API_KEY
# - DEBUG_MODE=false
```

### PASSO 5: Setup Database

```bash
cd backend

# Rodar migrations
alembic upgrade head

# Verificar
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect("data/tr4ction.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('template_definitions', 'fillable_fields')")
tables = cursor.fetchall()
print(f"✓ {len(tables)} tabelas encontradas") if len(tables) == 2 else print("✗ Tabelas não criadas")
conn.close()
EOF
```

### PASSO 6: Testar Backend

```bash
cd backend

# Iniciar
uvicorn main:app --host 0.0.0.0 --port 8000

# Em outro terminal, testar:
curl http://localhost:8000/health
# Esperado: {"status": "ok", ...}

# Testar FCJ
curl -X POST "http://localhost:8000/admin/templates/upload?cycle=Q1" \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@template.xlsx"
# Esperado: {"template_id": 1, "fields_count": ...}
```

### PASSO 7: Testar Frontend

```bash
cd frontend

# Criar .env.local
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://IP_PUBLICA:8000
EOF

# Instalar + Build
npm install
npm run build

# Testar
npm start
# Abrir browser: http://localhost:3000
```

### PASSO 8: Configurar Supervisão (systemd)

```bash
# Backend
sudo tee /etc/systemd/system/tr4ction-backend.service > /dev/null << 'EOF'
[Unit]
Description=TR4CTION Backend
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

# Frontend (alternativa: npm start)
sudo tee /etc/systemd/system/tr4ction-frontend.service > /dev/null << 'EOF'
[Unit]
Description=TR4CTION Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Tr4ction_Agent_V2/frontend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Habilitar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable tr4ction-backend.service
sudo systemctl enable tr4ction-frontend.service
sudo systemctl start tr4ction-backend.service
sudo systemctl start tr4ction-frontend.service

# Verificar status
sudo systemctl status tr4ction-backend.service
sudo systemctl status tr4ction-frontend.service
```

### PASSO 9: Validação Final

```bash
# Rodagem automática
python3 scripts/validate_production.py

# Checklist:
# ✓ Backend inicia
# ✓ Frontend inicia
# ✓ Database OK
# ✓ Nenhum erro nos logs
# ✓ Serviços com restart automático
# ✓ Reboot → serviços sobem

# Depois de reboot:
sudo reboot

# Aguardar 30s
sleep 30

# Verificar
curl http://localhost:8000/health
curl http://localhost:3000
```

---

## 🛑 SE ALGO DER ERRADO

### Backend não inicia
```bash
# Ver erro completo
cd backend && python3 main.py
# ou
journalctl -u tr4ction-backend.service -n 50 -f

# Verificar imports
python3 -c "from main import app"
# Se erro → voltar ao PASSO 3 (corrigir imports)

# Verificar .env
grep DATABASE_URL backend/.env
# Se vazio → corrigir em PASSO 4
```

### Frontend não inicia
```bash
# Ver erro
cd frontend && npm start

# Se erro de dependência
npm install --legacy-peer-deps

# Se erro de API
grep NEXT_PUBLIC_API_URL frontend/.env.local
# Deve apontar para IP correto
```

### Database não inicializa
```bash
# Rodar migrations novamente
cd backend && alembic upgrade head

# Se falha, fazer downgrade
alembic downgrade base
alembic upgrade head

# Verificar arquivo
ls -la data/tr4ction.db
```

---

## 📊 COMANDOS ÚTEIS

```bash
# Ver logs em tempo real
sudo journalctl -u tr4ction-backend.service -f

# Reiniciar backend
sudo systemctl restart tr4ction-backend.service

# Parar frontend
sudo systemctl stop tr4ction-frontend.service

# Ver processos
ps aux | grep uvicorn
ps aux | grep "npm start"

# Matar processo específico
pkill -f "uvicorn main:app"

# Ver portas abertas
sudo netstat -tlnp | grep LISTEN

# Espaço em disco
df -h

# Uso de memória
free -h

# Logs de startup
tail -100 backend/backend.log
tail -100 frontend/npm.log
```

---

## ⚠️ ERROS COMUNS

| Erro | Causa | Solução |
|------|-------|---------|
| `ModuleNotFoundError: backend.enterprise` | Import inválido | Corrigir em `backend/routers/founder.py` |
| `sqlite3.OperationalError: unable to open database file` | Path inválido | Verificar `DATABASE_URL` em `.env` |
| `CORS error` | API URL errada | Verificar `NEXT_PUBLIC_API_URL` em `frontend/.env.local` |
| `Port 8000 already in use` | Processo já rodando | `pkill -f "uvicorn main:app"` |
| `pip install error` | Dependência incompatível | `pip install --upgrade pip setuptools` |
| `npm ERR! peer dep` | Versão do Node incompatível | `npm install --legacy-peer-deps` |

---

## 📞 CONTATOS

- **Documentação Técnica:** [DEPLOYMENT_PLAN_PRODUCTION.md](DEPLOYMENT_PLAN_PRODUCTION.md)
- **Relatório Completo:** [RELATORIO_COMPLETO_PROJETO.md](RELATORIO_COMPLETO_PROJETO.md)
- **Sumário FCJ:** [CORE_FCJ_TEMPLATES_SUMMARY.md](CORE_FCJ_TEMPLATES_SUMMARY.md)

---

**SUCESSO = Todos os passos ✓ + teste final GO**

**Bom deploy! 🚀**
