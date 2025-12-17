# 🚀 TR4CTION Agent V2 - Backend

FastAPI backend com RAG (Retrieval-Augmented Generation) para análise de documentos e chat inteligente.

## ✨ Funcionalidades

- 🤖 **Chat Inteligente** - Integração com Groq LLM (llama-3.3-70b)
- 📚 **RAG Pipeline** - ChromaDB para busca semântica
- 📄 **Processamento de Documentos** - Suporte para PDF, PPTX, DOCX, TXT, XLSX
- 🔐 **Autenticação JWT** - Sistema seguro de login
- 👥 **Multi-tenancy** - Suporte para Admin e Founder roles
- 📊 **Exportação Excel** - Geração de relatórios
- 🔍 **Embeddings** - HuggingFace API ou local (sentence-transformers)
- 🛡️ **Segurança** - Rate limiting, CORS dinâmico, validação de input
- 📝 **Logging** - Sistema completo de logs

## 🚀 Quick Start

### Opção 1: Deploy Automático (Recomendado)
```bash
# Configurar .env
cp .env.example .env
nano .env  # Adicionar suas chaves de API

# Executar deploy
chmod +x deploy-ec2.sh
bash deploy-ec2.sh
```

### Opção 2: Manual
```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env com suas chaves

# Iniciar servidor
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📋 Guias Disponíveis

- **[QUICK_START.md](QUICK_START.md)** - Guia rápido (5 minutos)
- **[PRODUCTION_DEPLOY.md](PRODUCTION_DEPLOY.md)** - Deploy completo em produção
- **[AWS_SETUP.md](AWS_SETUP.md)** - Configuração AWS Security Group

## 🔧 Configuração

### Variáveis Obrigatórias (.env)
```env
GROQ_API_KEY=gsk_xxxxx                    # Obter em: https://console.groq.com/keys
HF_API_TOKEN=hf_xxxxx                     # Obter em: https://huggingface.co/settings/tokens
JWT_SECRET_KEY=xxxxx                      # Gerar com: openssl rand -hex 32
CORS_ORIGINS=https://seu-dominio.com
```

### Validar Configuração
```bash
python3 validate_env.py
```

## 🛠️ Scripts Disponíveis

| Script | Descrição | Uso |
|--------|-----------|-----|
| `deploy-ec2.sh` | Deploy automático | `bash deploy-ec2.sh` |
| `healthcheck.sh` | Verificar saúde da API | `bash healthcheck.sh [host] [port]` |
| `backup.sh` | Backup de databases | `bash backup.sh` |
| `validate_env.py` | Validar .env | `python3 validate_env.py` |

## 📊 Endpoints Principais

- `GET /` - Informações da API
- `GET /health` - Health check
- `GET /docs` - Documentação interativa (Swagger)
- `POST /auth/login` - Login
- `POST /chat/message` - Enviar mensagem ao chat
- `POST /files/upload` - Upload de arquivo
- `GET /admin/*` - Endpoints administrativos

## 🧪 Testes

```bash
# Health check
curl http://localhost:8000/health

# Verificação completa
bash healthcheck.sh localhost 8000

# Acessar documentação
open http://localhost:8000/docs
```

## 🔒 Segurança

- ✅ Rate limiting (100 req/min por padrão)
- ✅ CORS configurável via ambiente
- ✅ JWT com expiração configurável
- ✅ Validação de tamanho de upload
- ✅ Security headers automáticos
- ✅ Input sanitization

## 📦 Dependências Principais

- FastAPI 0.115.0
- Uvicorn 0.32.0
- ChromaDB 0.5.20
- Groq 0.14.0
- SQLAlchemy 2.0.23
- python-jose 3.3.0

Ver `requirements.txt` para lista completa.

## 🗂️ Estrutura do Projeto

```
backend/
├── main.py                 # Aplicação principal
├── config.py              # Configurações
├── core/                  # Módulos core
│   ├── logging_config.py
│   ├── middleware.py
│   ├── security.py
│   └── models.py
├── db/                    # Database
│   ├── database.py
│   └── models.py
├── routers/               # API routes
│   ├── auth.py
│   ├── chat.py
│   ├── admin.py
│   └── ...
├── services/              # Business logic
│   ├── rag_service.py
│   ├── embedding_service.py
│   ├── vector_store.py
│   └── ...
├── data/                  # Data storage
│   ├── chroma_db/
│   ├── uploads/
│   └── knowledge/
└── logs/                  # Application logs
```

## 🔄 Manutenção

### Backup
```bash
# Manual
bash backup.sh

# Automático (cron)
crontab -e
# Adicionar: 0 2 * * * /path/to/backup.sh
```

### Logs
```bash
# Ver logs da aplicação
tail -f logs/backend.log

# Logs de erro
tail -f logs/backend.error.log

# Logs do systemd (se configurado)
sudo journalctl -u tr4ction-backend -f
```

### Atualização
```bash
git pull origin main
pip install -r requirements.txt --upgrade
sudo systemctl restart tr4ction-backend
```

## 🆘 Troubleshooting

Ver seção completa em [PRODUCTION_DEPLOY.md](PRODUCTION_DEPLOY.md#troubleshooting)

**Problemas comuns:**
- Porta 8000 ocupada: `kill -9 $(lsof -t -i:8000)`
- Dependências: `pip install -r requirements.txt --force-reinstall`
- .env: `python3 validate_env.py`
- Logs: `tail -f logs/backend.log`

## 📝 Licença

Propriedade de TR4CTION.

## 🤝 Suporte

- GitHub Issues: https://github.com/lucasptrolesi-ai/Tr4ction-v2-Agent/issues
- Documentação: Ver arquivos DEPLOY_*.md
- Logs: `logs/backend.log
