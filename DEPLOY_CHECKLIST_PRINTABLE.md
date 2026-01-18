# ✅ CHECKLIST DEPLOY FINAL - VERSÃO EXECUTIVA

**Imprima este documento e use durante o deploy!**

---

## 📋 CHECKLIST PRÉ-DEPLOY (Fazer localmente)

### Leitura & Entendimento
- [ ] Lido DEPLOYMENT_PLAN_PRODUCTION.md completamente
- [ ] Entendi os 11 passos
- [ ] Anotei as variáveis críticas de .env
- [ ] Verificada infra AWS disponível

### Validação Local (PRECHECK_DEPLOY.md)
- [ ] Verificação 1: Python version ✓
- [ ] Verificação 2: Node version ✓
- [ ] Verificação 3: Git status ✓
- [ ] Verificação 4: venv criado ✓
- [ ] Verificação 5: pip packages ✓
- [ ] Verificação 6: Database exists ✓
- [ ] Verificação 7: Alembic current ✓
- [ ] Verificação 8: Imports test ✓
- [ ] Verificação 9: Storage dirs ✓
- [ ] Verificação 10: .env vars ✓

### Infraestrutura AWS
- [ ] EC2 t3.small provisionada
- [ ] Ubuntu 22.04 LTS
- [ ] Security groups: 22 (SSH), 80 (HTTP), 443 (HTTPS)
- [ ] Chaves SSH configuradas
- [ ] Elastic IP associado (opcional)
- [ ] RDS/Database provisionado (se necessário)

---

## 📋 CHECKLIST DEPLOY (Na EC2)

### Setup Inicial
- [ ] SSH conectado com sucesso
- [ ] Internet funcionando: `ping 8.8.8.8`
- [ ] Espaço em disco: `df -h` → > 20%
- [ ] Permissões OK: `whoami` → não é root

### Clone & Setup
- [ ] git clone efetuado: `cd Tr4ction_Agent_V2`
- [ ] git branch correto: `git status` → main
- [ ] venv criado: `python3 -m venv venv`
- [ ] venv ativado: `source venv/bin/activate`
- [ ] pip atualizado: `pip install --upgrade pip`
- [ ] requirements instalado: `pip install -r backend/requirements.txt`

### Auditoria (bash script)
```bash
bash scripts/deploy_audit.sh
```
- [ ] Comando executado sem erro
- [ ] Log gerado: `/tmp/tr4ction_deploy_audit_*.log`
- [ ] Resultado: **GO ✓** (todos os itens verde)
- Se **✗**: Consultar erro + CORRIGIR antes de continuar

### Validação Python
```bash
python3 scripts/validate_production.py
```
- [ ] Teste 1 - .env: ✓
- [ ] Teste 2 - Database: ✓
- [ ] Teste 3 - Backend startup: ✓
- [ ] Teste 4 - Storage: ✓
- [ ] Teste 5 - Imports: ✓
- [ ] Teste 6 - Alembic: ✓
- [ ] Resultado final: **GO / DEPLOY APROVADO**
- Se **NO-GO**: Consultar detalhe + CORRIGIR antes de continuar

---

## 📋 CHECKLIST DEPLOYMENT (Systemd Setup)

### Criar serviço Backend
```bash
sudo nano /etc/systemd/system/tr4ction-backend.service
```
- [ ] Arquivo criado
- [ ] ExecStart apontando correto: `ExecStart=/home/ubuntu/venv/bin/python main.py`
- [ ] WorkingDirectory correto
- [ ] Restart sempre ativo: `Restart=always`
- [ ] User não é root

### Criar serviço Frontend
```bash
sudo nano /etc/systemd/system/tr4ction-frontend.service
```
- [ ] Arquivo criado
- [ ] ExecStart: `npm start`
- [ ] WorkingDirectory apontando certo
- [ ] Restart=always configurado

### Habilitar & Iniciar
```bash
sudo systemctl daemon-reload
sudo systemctl enable tr4ction-backend.service
sudo systemctl enable tr4ction-frontend.service
sudo systemctl start tr4ction-backend.service
sudo systemctl start tr4ction-frontend.service
```
- [ ] daemon-reload executado
- [ ] Serviços habilitados para boot
- [ ] Serviços iniciados
- [ ] Status backend: `sudo systemctl status tr4ction-backend`
- [ ] Status frontend: `sudo systemctl status tr4ction-frontend`
- [ ] Ambos mostrando: **active (running)**

---

## 📋 CHECKLIST VALIDAÇÃO PÓS-DEPLOY

### Health Checks
```bash
curl http://localhost:8000/health
curl http://localhost:3000
curl http://IP-DA-EC2:8000/health
```
- [ ] Backend health: 200 OK
- [ ] Frontend: 200 OK (HTML)
- [ ] Acessível via IP público

### Teste FCJ (Critical)
```bash
curl -X POST http://localhost:8000/admin/templates/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.json"
```
- [ ] Comando executou (ou teste alternativo)
- [ ] Response 200/201
- [ ] Snapshot gerado
- [ ] Fillable fields > 0

### Logs
```bash
journalctl -u tr4ction-backend.service -n 50
journalctl -u tr4ction-frontend.service -n 50
```
- [ ] Nenhum ERROR em logs
- [ ] Nenhum CRITICAL
- [ ] Warnings OK (investigar depois se necessário)
- [ ] Últimas linhas = normal startup messages

### Reboot Automático (CRITICAL)
```bash
sudo reboot
# Esperar 2 minutos
curl http://IP:8000/health
sudo systemctl status tr4ction-backend
```
- [ ] EC2 rebootou
- [ ] Backend subiu sozinho (restart policy)
- [ ] curl health responde 200
- [ ] systemctl mostra active/running
- [ ] Nenhuma ação manual necessária

---

## 📋 CHECKLIST MONITORAMENTO (24h após deploy)

### Hora 1 (Imediato)
- [ ] Logs limpos (sem erros)
- [ ] CPU normal (< 50%)
- [ ] Memory normal (< 60%)
- [ ] Disk OK (> 20% livre)

### Hora 6
- [ ] Sistema ainda respondendo
- [ ] Nenhum erro novo nos logs
- [ ] Processamento normal

### Hora 12
- [ ] Carga normal
- [ ] Sem memory leaks
- [ ] Sem file descriptor leaks

### Hora 24
- [ ] Sistema estável
- [ ] Pronto para usuários
- [ ] Alertas configurados

---

## 🚨 ERROS CRÍTICOS - NÃO PROSSEGUIR

Se encontrar QUALQUER um desses, PARAR e INVESTIGAR:

### Backend
- [ ] ❌ ModuleNotFoundError
- [ ] ❌ ImportError
- [ ] ❌ PermissionError
- [ ] ❌ Database connection failed
- [ ] ❌ Port already in use

### Frontend
- [ ] ❌ npm install error
- [ ] ❌ Build failed
- [ ] ❌ Port 3000 occupied

### Database
- [ ] ❌ Migration failed
- [ ] ❌ Table not found
- [ ] ❌ Connection refused

### Systemd
- [ ] ❌ Failed to start service
- [ ] ❌ Restart loop (> 5 restarts/min)
- [ ] ❌ Cannot write to log file

---

## 📊 VARIÁVEIS CRÍTICAS .env

Anotar ANTES de deploy:

```
DATABASE_URL=
JWT_SECRET= (min 32 chars)
DEBUG_MODE=false (IMPORTANTE: sempre false em prod)
ALLOWED_HOSTS=
CORS_ORIGINS=
UPLOAD_DIR=
LOG_LEVEL=INFO
```

Validar com `python3 scripts/validate_production.py`:
- [ ] DATABASE_URL não vazio
- [ ] JWT_SECRET >= 32 chars
- [ ] DEBUG_MODE=false
- [ ] Todos as dirs existem

---

## 🎯 GO/NO-GO FINAL

### Go (Liberar para usuários)
Todas as seguintes são ✓:
- [ ] deploy_audit.sh = GO
- [ ] validate_production.py = DEPLOY APROVADO
- [ ] curl health = 200
- [ ] Upload FCJ funciona
- [ ] Reboot automático validado
- [ ] 24h monitoramento = estável
- [ ] Nenhum erro crítico

**Resultado:** ✅ **LIBERAR PARA USUÁRIOS**

### No-Go (Parar & Corrigir)
Se qualquer um é ✗:
- [ ] Parar deployment imediatamente
- [ ] Investigar erro específico
- [ ] Consultar: DEPLOY_QUICK_REFERENCE.md → Error Table
- [ ] Executar fix
- [ ] Re-validar com scripts
- [ ] Só depois: continuar

**Resultado:** 🚫 **NÃO LIBERAR** → CORRIGIR ANTES

---

## 📞 REFERÊNCIA RÁPIDA DE COMANDOS

### Informações Sistema
```bash
uname -a                           # SO info
df -h                             # Disco
free -h                           # Memória
ps aux | grep tr4ction           # Processos
```

### Logs
```bash
journalctl -u tr4ction-backend.service -f       # Real-time
journalctl -u tr4ction-backend.service -n 100   # Últimas 100
tail -f /var/log/tr4ction/backend.log          # Se arquivo
```

### Serviços
```bash
sudo systemctl status tr4ction-backend           # Status
sudo systemctl restart tr4ction-backend          # Reiniciar
sudo systemctl stop tr4ction-backend             # Parar
sudo systemctl start tr4ction-backend            # Iniciar
```

### Health Check
```bash
curl http://localhost:8000/health
curl http://localhost:3000
curl -v http://IP:8000/health                   # Verbose
```

### Deploy Audit
```bash
bash scripts/deploy_audit.sh
cat /tmp/tr4ction_deploy_audit_*.log
```

### Validation
```bash
python3 scripts/validate_production.py
```

---

## 🔒 SEGURANÇA PRÉ-DEPLOY

- [ ] DEBUG_MODE=false confirmado
- [ ] JWT_SECRET >= 32 chars aleatórios
- [ ] SSL certificates provisionados (Let's Encrypt)
- [ ] CORS_ORIGINS configurado (não *_
- [ ] ALLOWED_HOSTS configurado correto
- [ ] Senhas/secrets em .env (não em código)
- [ ] Permissões de arquivo corretas (600 para .env)

---

## 📝 NOTAS IMPORTANTES

**Este checklist é seu guia durante o deploy.**

1. Imprima este documento
2. Marque cada item enquanto executa
3. Anotar qualquer desvio
4. Se algo falha: PARAR e investigar
5. Não ignorar warnings
6. Testar completamente antes de liberar

---

## 📌 PRÓXIMA ETAPA

- [ ] Impresso este checklist ✅
- [ ] Pronto para iniciar deploy
- [ ] Equipe informada (ETA: ~6 horas)
- [ ] Monitoramento configurado
- [ ] Rollback procedure pronto

---

**Data:** 14 de janeiro de 2026  
**Versão:** 1.0  
**Preparado por:** GitHub Copilot (SRE Mode)

**Bom deploy! 🚀**
