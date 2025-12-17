# 🚀 TR4CTION Agent V2 - Instruções de Deploy

## 📖 Começar Aqui

Este guia mostra como colocar o backend do TR4CTION Agent V2 em produção em **5-10 minutos**.

---

## ✅ Status Atual

O backend está **100% pronto para produção**:
- ✅ Código revisado e testado
- ✅ Scripts de automação criados
- ✅ Documentação completa disponível
- ✅ Todos os 7 erros críticos corrigidos

---

## 🎯 O Que Você Precisa Fazer

### 1️⃣ Obter Chaves de API (5 min)

**Groq API Key** (Obrigatória):
- Acesse: https://console.groq.com/keys
- Crie uma conta gratuita
- Gere uma API key
- Formato: `gsk_xxxxxxxxxxxxxxxxxxxxx`

**HuggingFace Token** (Recomendado):
- Acesse: https://huggingface.co/settings/tokens
- Faça login ou crie conta
- Gere um token de leitura
- Formato: `hf_xxxxxxxxxxxxxxxxxxxxx`

### 2️⃣ Configurar .env (2 min)

**SSH na sua instância EC2:**
```bash
ssh -i sua-chave.pem ubuntu@SEU_IP_EC2
```

**Configurar .env:**
```bash
cd ~/Tr4ction-v2-Agent/backend
cp .env.example .env
nano .env
```

**Editar estas linhas:**
```env
GROQ_API_KEY=gsk_COLE_SUA_CHAVE_AQUI
HF_API_TOKEN=hf_COLE_SUA_CHAVE_AQUI
JWT_SECRET_KEY=GERE_COM_OPENSSL_ABAIXO
CORS_ORIGINS=https://seu-dominio.com,http://localhost:3000
```

**Gerar JWT Secret:**
```bash
openssl rand -hex 32
# Copie o resultado e cole no .env
```

Salvar: `Ctrl + O`, Enter, `Ctrl + X`

### 3️⃣ Liberar Porta 8000 na AWS (2 min)

1. Acesse AWS Console: https://console.aws.amazon.com
2. Vá para **EC2** → **Instances**
3. Selecione sua instância
4. Aba **"Security"** → Clicar no Security Group
5. **"Edit inbound rules"** → **"Add rule"**
6. Configurar:
   - Type: `Custom TCP`
   - Port: `8000`
   - Source: `0.0.0.0/0`
   - Description: `TR4CTION Backend`
7. Clicar em **"Save rules"**

### 4️⃣ Executar Deploy (1 min)

**Na EC2 via SSH:**
```bash
cd ~/Tr4ction-v2-Agent/backend
bash deploy-ec2.sh
```

O script vai:
- ✅ Verificar Python e dependências
- ✅ Criar ambiente virtual
- ✅ Instalar dependências
- ✅ Validar configuração
- ✅ Iniciar o backend

### 5️⃣ Verificar (1 min)

**Teste local:**
```bash
curl http://localhost:8000/health
```

**Teste externo (do seu computador):**
```bash
curl http://SEU_IP_EC2:8000/health
```

**Resposta esperada:**
```json
{"status":"ok"}
```

**Abrir no navegador:**
```
http://SEU_IP_EC2:8000/docs
```

---

## 🎉 Pronto!

Se você viu `{"status":"ok"}`, seu backend está rodando em produção!

---

## 📚 Documentação Completa

Para mais detalhes, consulte:

- **[QUICK_START.md](backend/QUICK_START.md)** - Guia rápido (5 min)
- **[PRODUCTION_DEPLOY.md](backend/PRODUCTION_DEPLOY.md)** - Guia completo
- **[AWS_SETUP.md](backend/AWS_SETUP.md)** - Detalhes AWS Security Group
- **[BACKEND_PRODUCTION_STATUS.md](BACKEND_PRODUCTION_STATUS.md)** - Relatório completo

---

## 🔄 Rodar em Background

Para que o backend continue rodando após fechar SSH:

```bash
# Pressione Ctrl+C para parar o processo atual

# Rode em background
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > logs/backend.log 2>&1 &

# Verificar que está rodando
ps aux | grep uvicorn
```

---

## 🤖 Auto-start (Opcional)

Para iniciar automaticamente após reboot:

```bash
# Instalar service do systemd
sudo cp tr4ction-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tr4ction-backend
sudo systemctl start tr4ction-backend

# Verificar status
sudo systemctl status tr4ction-backend
```

---

## 🆘 Problemas?

### Backend não inicia
```bash
# Ver logs
tail -f logs/backend.log

# Verificar .env
python3 validate_env.py

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Não consigo acessar de fora
```bash
# Verificar se está rodando
ps aux | grep uvicorn

# Verificar porta
lsof -i :8000

# Verificar firewall
sudo ufw status
```

### Porta 8000 ocupada
```bash
# Parar processo
kill -9 $(lsof -t -i:8000)

# Reiniciar
bash deploy-ec2.sh
```

### Mais ajuda
- Ver logs: `tail -f logs/backend.log`
- Health check: `bash healthcheck.sh`
- Validar .env: `python3 validate_env.py`
- Documentação completa: `backend/PRODUCTION_DEPLOY.md`

---

## 📊 Scripts Disponíveis

| Script | Comando | Descrição |
|--------|---------|-----------|
| Deploy | `bash deploy-ec2.sh` | Deploy automático |
| Health Check | `bash healthcheck.sh` | Verificar saúde |
| Backup | `bash backup.sh` | Backup de dados |
| Validar .env | `python3 validate_env.py` | Validar config |

---

## 🎯 Checklist Rápido

- [ ] Chaves de API obtidas (Groq + HuggingFace)
- [ ] .env configurado na EC2
- [ ] Porta 8000 liberada no AWS Security Group
- [ ] Script deploy-ec2.sh executado
- [ ] curl localhost:8000/health retorna OK
- [ ] curl SEU_IP:8000/health retorna OK (de fora da EC2)
- [ ] /docs acessível no navegador

**Se todos marcados ✅, está pronto para produção!** 🚀

---

## 🔗 Links Úteis

- **Groq Console**: https://console.groq.com/keys
- **HuggingFace**: https://huggingface.co/settings/tokens
- **AWS Console**: https://console.aws.amazon.com
- **GitHub**: https://github.com/lucasptrolesi-ai/Tr4ction-v2-Agent

---

## ✨ Resumo

```
Tempo total: 5-10 minutos
Dificuldade: ⭐⭐ (Fácil)
Resultado: Backend rodando em produção

Status: ✅ READY FOR PRODUCTION
```

---

*Última atualização: 17 de Dezembro de 2025*  
*Versão: 2.0.0*
