# 🚀 TR4CTION Agent V2 - Guia de Deploy em Produção

## 📋 Índice
1. [Pré-requisitos](#pré-requisitos)
2. [Deploy Rápido (5 minutos)](#deploy-rápido)
3. [Deploy Completo com Systemd](#deploy-completo)
4. [Configuração AWS Security Group](#configuração-aws)
5. [Verificação e Testes](#verificação)
6. [Troubleshooting](#troubleshooting)
7. [Manutenção](#manutenção)

---

## 🎯 Pré-requisitos

### Servidor AWS EC2
- ✅ Instância EC2 ativa (t3.micro ou superior)
- ✅ Sistema operacional: Ubuntu 20.04+ ou Amazon Linux 2
- ✅ Acesso SSH configurado
- ✅ Porta 8000 liberada no Security Group

### Chaves de API Necessárias
- 🔑 **Groq API Key** (obrigatória)
  - Obter em: https://console.groq.com/keys
  - Formato: `gsk_xxxxxxxxxxxxxxxxxxxxx`
  
- 🔑 **HuggingFace Token** (recomendado)
  - Obter em: https://huggingface.co/settings/tokens
  - Formato: `hf_xxxxxxxxxxxxxxxxxxxxx`

### Software Necessário no Servidor
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python e ferramentas
sudo apt install python3 python3-pip python3-venv git curl -y

# Verificar instalação
python3 --version  # Deve ser Python 3.8+
pip3 --version
```

---

## ⚡ Deploy Rápido (5 minutos)

### Passo 1: Clonar o Repositório
```bash
cd ~
git clone https://github.com/lucasptrolesi-ai/Tr4ction-v2-Agent.git
cd Tr4ction-v2-Agent/backend
```

### Passo 2: Configurar .env
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com suas chaves
nano .env
```

**Configurações OBRIGATÓRIAS no .env:**
```env
# LLM Provider
GROQ_API_KEY=gsk_SUA_CHAVE_AQUI

# Embeddings (escolha uma opção)
EMBEDDING_PROVIDER=huggingface
HF_API_TOKEN=hf_SUA_CHAVE_AQUI

# Security (MUDE EM PRODUÇÃO!)
JWT_SECRET_KEY=gere-uma-chave-segura-com-openssl-rand-hex-32

# CORS - Adicione seus domínios
CORS_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
```

**Gerar JWT Secret seguro:**
```bash
openssl rand -hex 32
# Copie o resultado para JWT_SECRET_KEY no .env
```

### Passo 3: Executar Deploy
```bash
# Dar permissão de execução
chmod +x deploy-ec2.sh

# Executar script de deploy
bash deploy-ec2.sh
```

✅ **Se tudo correr bem, o backend estará rodando em http://SEU_IP:8000**

### Passo 4: Verificar Health Check
```bash
# Tornar executável
chmod +x healthcheck.sh

# Executar verificação
bash healthcheck.sh localhost 8000
```

Resposta esperada:
```
✅ [OK] Backend está rodando corretamente!
```

---

## 🔧 Deploy Completo com Systemd

Para garantir que o backend inicie automaticamente após reinicialização:

### Passo 1: Configurar Service File
```bash
# Editar caminhos no arquivo (se necessário)
nano tr4ction-backend.service

# Ajustar User, Group e WorkingDirectory conforme sua instalação
```

### Passo 2: Instalar Service
```bash
# Copiar para systemd
sudo cp tr4ction-backend.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar inicialização automática
sudo systemctl enable tr4ction-backend

# Iniciar serviço
sudo systemctl start tr4ction-backend

# Verificar status
sudo systemctl status tr4ction-backend
```

### Passo 3: Comandos Úteis do Systemd
```bash
# Ver logs em tempo real
sudo journalctl -u tr4ction-backend -f

# Reiniciar serviço
sudo systemctl restart tr4ction-backend

# Parar serviço
sudo systemctl stop tr4ction-backend

# Ver status
sudo systemctl status tr4ction-backend
```

---

## 🔐 Configuração AWS Security Group

### Adicionar Regra de Entrada (Inbound Rule)

1. **Acessar AWS Console**
   - Ir para EC2 > Instances
   - Selecionar sua instância
   - Clicar na aba "Security"
   - Clicar no Security Group ativo

2. **Adicionar Regra**
   - Clicar em "Edit inbound rules"
   - Clicar em "Add rule"
   
3. **Configurar Regra**
   ```
   Type: Custom TCP
   Protocol: TCP
   Port Range: 8000
   Source: 0.0.0.0/0 (ou específico para seu IP)
   Description: TR4CTION Backend API
   ```

4. **Salvar Regras**
   - Clicar em "Save rules"

### Teste de Conectividade
```bash
# Do seu computador local
curl http://SEU_IP_EC2:8000/health

# Deve retornar: {"status":"ok"}
```

---

## ✅ Verificação e Testes

### 1. Teste Local (dentro da EC2)
```bash
# Health check
curl http://localhost:8000/health

# Endpoint raiz
curl http://localhost:8000/

# Documentação da API
curl http://localhost:8000/docs
```

### 2. Teste Externo (do seu computador)
```bash
# Obter IP público da EC2
curl http://checkip.amazonaws.com

# Testar endpoint
curl http://SEU_IP_PUBLICO:8000/health
```

### 3. Teste pelo Browser
Abrir no navegador:
- `http://SEU_IP_PUBLICO:8000/` - Página raiz
- `http://SEU_IP_PUBLICO:8000/docs` - Documentação interativa
- `http://SEU_IP_PUBLICO:8000/health` - Health check

### 4. Verificar Logs
```bash
# Logs do aplicativo
tail -f logs/backend.log

# Logs de erro
tail -f logs/backend.error.log

# Logs do systemd (se configurado)
sudo journalctl -u tr4ction-backend -f
```

---

## 🔍 Troubleshooting

### Problema 1: Backend não inicia
```bash
# Verificar erros de sintaxe
python3 -c "import main; print('OK')"

# Verificar dependências
pip3 list | grep -E "fastapi|uvicorn|chromadb|groq"

# Reinstalar dependências
pip3 install -r requirements.txt --force-reinstall
```

### Problema 2: Erro de importação
```bash
# Verificar ambiente virtual
which python3

# Ativar ambiente virtual
source venv/bin/activate

# Reinstalar dependências no venv
pip install -r requirements.txt
```

### Problema 3: Porta 8000 ocupada
```bash
# Verificar processo na porta 8000
lsof -i :8000

# Parar processo
kill -9 $(lsof -t -i:8000)

# Ou usar outra porta
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### Problema 4: Variáveis de ambiente não carregadas
```bash
# Verificar se .env existe
ls -la .env

# Validar .env
python3 validate_env.py

# Testar manualmente
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GROQ_API_KEY'))"
```

### Problema 5: ChromaDB não inicializa
```bash
# Verificar diretório
ls -la data/chroma_db/

# Recriar diretório
rm -rf data/chroma_db/*
mkdir -p data/chroma_db

# Reiniciar backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Problema 6: CORS bloqueando requisições
Editar `.env`:
```env
CORS_ORIGINS=https://seu-dominio.com,http://localhost:3000,http://SEU_IP:8000
```

### Problema 7: API Key inválida
```bash
# Verificar formato da chave
cat .env | grep GROQ_API_KEY

# Testar chave manualmente
curl -H "Authorization: Bearer gsk_SUA_CHAVE" https://api.groq.com/openai/v1/models
```

---

## 🔄 Manutenção

### Backup do Banco de Dados
```bash
# Criar diretório de backups
mkdir -p ~/backups

# Backup do SQLite
cp tr4ction.db ~/backups/tr4ction-$(date +%Y%m%d-%H%M%S).db

# Backup do ChromaDB
tar -czf ~/backups/chroma-$(date +%Y%m%d-%H%M%S).tar.gz data/chroma_db/
```

### Script de Backup Automático
Criar arquivo `backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR=~/backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d-%H%M%S)

# Backup databases
cp /home/ubuntu/Tr4ction-v2-Agent/backend/tr4ction.db $BACKUP_DIR/tr4ction-$DATE.db
tar -czf $BACKUP_DIR/chroma-$DATE.tar.gz -C /home/ubuntu/Tr4ction-v2-Agent/backend data/chroma_db/

# Limpar backups antigos (manter apenas últimos 7 dias)
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup concluído: $DATE"
```

Agendar com cron:
```bash
# Editar crontab
crontab -e

# Adicionar linha (backup diário às 2h da manhã)
0 2 * * * /home/ubuntu/backup.sh >> /home/ubuntu/backup.log 2>&1
```

### Atualização do Código
```bash
# Parar backend
sudo systemctl stop tr4ction-backend

# Backup antes da atualização
cp -r ~/Tr4ction-v2-Agent ~/Tr4ction-v2-Agent.backup

# Atualizar código
cd ~/Tr4ction-v2-Agent
git pull origin main

# Atualizar dependências
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Reiniciar backend
sudo systemctl start tr4ction-backend

# Verificar status
sudo systemctl status tr4ction-backend
```

### Monitoramento
```bash
# Verificar uso de memória
free -h

# Verificar uso de disco
df -h

# Verificar processos Python
ps aux | grep python

# Monitorar logs em tempo real
tail -f logs/backend.log
```

---

## 📊 Checklist de Deploy

### Antes do Deploy
- [ ] Chave GROQ_API_KEY obtida e configurada
- [ ] Token HF_API_TOKEN obtido (opcional)
- [ ] JWT_SECRET_KEY gerado (openssl rand -hex 32)
- [ ] CORS_ORIGINS configurado com domínios de produção
- [ ] Security Group AWS configurado (porta 8000)
- [ ] Instância EC2 rodando e acessível via SSH

### Durante o Deploy
- [ ] Código clonado do GitHub
- [ ] .env configurado com chaves reais
- [ ] Dependências instaladas (requirements.txt)
- [ ] Diretórios criados (data/, uploads/, logs/)
- [ ] Backend iniciado com sucesso

### Após o Deploy
- [ ] Health check retornando {"status":"ok"}
- [ ] API acessível externamente (http://IP:8000/docs)
- [ ] Logs sendo gerados corretamente
- [ ] Systemd configurado (opcional)
- [ ] Backup agendado (opcional)
- [ ] Monitoramento configurado (opcional)

---

## 🆘 Suporte

### Logs Importantes
- `logs/backend.log` - Logs da aplicação
- `logs/backend.error.log` - Erros da aplicação
- `sudo journalctl -u tr4ction-backend` - Logs do systemd

### Comandos de Diagnóstico
```bash
# Status completo do sistema
bash healthcheck.sh localhost 8000

# Validar configuração
python3 validate_env.py

# Testar importações
python3 -c "import fastapi, uvicorn, chromadb, groq; print('OK')"

# Verificar porta
netstat -tuln | grep 8000
```

### Contato
- GitHub Issues: https://github.com/lucasptrolesi-ai/Tr4ction-v2-Agent/issues
- Documentação: Ver arquivos DEPLOY_*.md no repositório

---

## ✨ Conclusão

Seguindo este guia, seu backend TR4CTION Agent V2 estará:
- ✅ Rodando em produção na AWS EC2
- ✅ Configurado com systemd para reinício automático
- ✅ Monitorado via logs
- ✅ Protegido com Security Group
- ✅ Pronto para receber requisições do frontend

**Próximo passo:** Configurar frontend no Vercel para conectar ao backend.
