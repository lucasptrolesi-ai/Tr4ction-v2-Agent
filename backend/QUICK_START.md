# ⚡ TR4CTION Agent V2 - Quick Start Guide

## 🎯 Para Colocar em Produção em 5 Minutos

### ✅ O que já está PRONTO
- ✅ Código revisado e sem erros de sintaxe
- ✅ Dependências testadas e compatíveis
- ✅ CORS configurado dinamicamente
- ✅ ChromaDB consolidado e funcionando
- ✅ Embedding service com fallback
- ✅ Database inicializa automaticamente
- ✅ Scripts de deploy criados
- ✅ Documentação completa

### 🟡 O que VOCÊ precisa fazer

#### 1️⃣ Configurar Chaves de API (2 min)

**No servidor EC2 via SSH:**
```bash
cd ~/Tr4ction-v2-Agent/backend
cp .env.example .env
nano .env
```

**Editar estas linhas no .env:**
```env
# Obrigatório - Obter em: https://console.groq.com/keys
GROQ_API_KEY=gsk_SUA_CHAVE_REAL_AQUI

# Recomendado - Obter em: https://huggingface.co/settings/tokens
HF_API_TOKEN=hf_SUA_CHAVE_REAL_AQUI

# Segurança - Gerar com: openssl rand -hex 32
JWT_SECRET_KEY=COLE_RESULTADO_DO_OPENSSL_AQUI

# CORS - Adicionar seus domínios
CORS_ORIGINS=https://tr4ction-v2-agent.vercel.app,http://localhost:3000
```

Salvar: `Ctrl + O`, Enter, `Ctrl + X`

#### 2️⃣ Liberar Porta 8000 na AWS (1 min)

**No AWS Console:**
1. EC2 → Instances → Selecionar sua instância
2. Aba "Security" → Clicar no Security Group
3. "Edit inbound rules" → "Add rule"
4. Configurar:
   - Type: **Custom TCP**
   - Port: **8000**
   - Source: **0.0.0.0/0**
   - Description: **TR4CTION Backend**
5. "Save rules"

#### 3️⃣ Executar Deploy (2 min)

**No servidor EC2 via SSH:**
```bash
cd ~/Tr4ction-v2-Agent/backend

# Dar permissão aos scripts
chmod +x deploy-ec2.sh healthcheck.sh

# Executar deploy
bash deploy-ec2.sh
```

**Pronto! O backend vai iniciar automaticamente.**

---

## ✅ Verificação Rápida

### Teste 1: Health Check Local
```bash
curl http://localhost:8000/health
```
**Esperado:** `{"status":"ok"}`

### Teste 2: Health Check Externo
```bash
# Substituir SEU_IP pelo IP público da EC2
curl http://SEU_IP:8000/health
```
**Esperado:** `{"status":"ok"}`

### Teste 3: Documentação da API
Abrir no navegador:
```
http://SEU_IP:8000/docs
```

---

## 🔄 Para Rodar em Background

Depois que o deploy funcionar, pressione `Ctrl + C` e execute:

```bash
# Rodar em background com logs
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > logs/backend.log 2>&1 &

# Verificar que está rodando
ps aux | grep uvicorn
```

---

## 🤖 (Opcional) Configurar Systemd

Para inicialização automática após reboot:

```bash
# Ajustar caminhos no service file (se necessário)
nano tr4ction-backend.service

# Instalar serviço
sudo cp tr4ction-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tr4ction-backend
sudo systemctl start tr4ction-backend

# Verificar status
sudo systemctl status tr4ction-backend
```

---

## 🆘 Se Algo Der Errado

### Erro: "Module not found"
```bash
cd ~/Tr4ction-v2-Agent/backend
source venv/bin/activate
pip install -r requirements.txt
```

### Erro: "Port 8000 already in use"
```bash
# Parar processo existente
kill -9 $(lsof -t -i:8000)

# Reiniciar
bash deploy-ec2.sh
```

### Erro: "Cannot connect to backend"
```bash
# Verificar se está rodando
ps aux | grep uvicorn

# Verificar logs
tail -f logs/backend.log

# Verificar porta
netstat -tuln | grep 8000
```

### Erro: ".env validation failed"
```bash
# Validar configuração
python3 validate_env.py

# Verificar chaves
cat .env | grep -E "GROQ|HF_API"
```

---

## 📊 Comandos Úteis

```bash
# Ver logs em tempo real
tail -f logs/backend.log

# Verificar saúde
bash healthcheck.sh localhost 8000

# Parar backend
pkill -f uvicorn

# Reiniciar backend
bash deploy-ec2.sh

# Ver processos
ps aux | grep python

# Verificar porta
lsof -i :8000
```

---

## 🎯 Próximos Passos

Após backend em produção:

1. ✅ Testar todos os endpoints via /docs
2. ✅ Conectar frontend (Vercel) ao backend
3. ✅ Fazer upload de documentos de conhecimento
4. ✅ Testar chat com o agente
5. ✅ Configurar backups automáticos (opcional)
6. ✅ Configurar SSL/HTTPS (opcional)

---

## 📚 Documentação Completa

- **Deploy Completo**: `PRODUCTION_DEPLOY.md`
- **AWS Security Group**: `AWS_SETUP.md`
- **Troubleshooting**: Ver seção "Troubleshooting" em `PRODUCTION_DEPLOY.md`

---

## ✨ Checklist Final

- [ ] .env configurado com chaves reais
- [ ] Porta 8000 liberada no AWS Security Group
- [ ] Backend rodando (curl localhost:8000/health retorna OK)
- [ ] Backend acessível externamente (curl SEU_IP:8000/health retorna OK)
- [ ] API Docs acessível (http://SEU_IP:8000/docs)
- [ ] (Opcional) Systemd configurado para auto-start

**Se todos os itens acima estiverem ✅, seu backend está PRONTO PARA PRODUÇÃO! 🚀**

---

## 📞 Suporte

- Logs: `tail -f logs/backend.log`
- Health: `bash healthcheck.sh`
- Validação: `python3 validate_env.py`
- GitHub Issues: https://github.com/lucasptrolesi-ai/Tr4ction-v2-Agent/issues

---

**Tempo estimado total: 5-10 minutos**
**Dificuldade: ⭐⭐ (Fácil)**
