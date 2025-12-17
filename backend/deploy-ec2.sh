#!/bin/bash
# ======================================================
# TR4CTION Agent V2 - Script de Deploy Automático EC2
# ======================================================
# Este script automatiza o deploy do backend na AWS EC2
# Uso: bash deploy-ec2.sh

set -e

echo "🚀 =========================================="
echo "   TR4CTION Agent V2 - Deploy EC2"
echo "=========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logs coloridos
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ======================================================
# 1. Verificar se estamos no diretório backend
# ======================================================
if [ ! -f "main.py" ]; then
    log_error "Arquivo main.py não encontrado!"
    log_info "Execute este script a partir do diretório backend/"
    exit 1
fi

log_success "Diretório correto detectado"

# ======================================================
# 2. Verificar arquivo .env
# ======================================================
if [ ! -f ".env" ]; then
    log_warn "Arquivo .env não encontrado!"
    log_info "Copiando .env.example para .env..."
    cp .env.example .env
    log_warn "IMPORTANTE: Edite o arquivo .env com suas chaves de API reais!"
    log_info "Execute: nano .env"
    exit 1
fi

log_success "Arquivo .env encontrado"

# ======================================================
# 3. Validar configuração do .env
# ======================================================
log_info "Validando configuração do .env..."
if command -v python3 &> /dev/null; then
    python3 validate_env.py
    if [ $? -ne 0 ]; then
        log_error "Validação do .env falhou!"
        log_info "Corrija os problemas no arquivo .env antes de continuar"
        exit 1
    fi
else
    log_warn "Python3 não encontrado, pulando validação do .env"
fi

# ======================================================
# 4. Verificar Python e pip
# ======================================================
log_info "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    log_error "Python3 não instalado!"
    log_info "Instale com: sudo apt update && sudo apt install python3 python3-pip -y"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
log_success "Python encontrado: $PYTHON_VERSION"

# ======================================================
# 5. Criar/ativar ambiente virtual
# ======================================================
log_info "Configurando ambiente virtual..."
if [ ! -d "venv" ]; then
    log_info "Criando novo ambiente virtual..."
    python3 -m venv venv
    log_success "Ambiente virtual criado"
fi

log_info "Ativando ambiente virtual..."
source venv/bin/activate
log_success "Ambiente virtual ativado"

# ======================================================
# 6. Instalar dependências
# ======================================================
log_info "Instalando/atualizando dependências..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
log_success "Dependências instaladas"

# ======================================================
# 7. Criar diretórios necessários
# ======================================================
log_info "Criando diretórios necessários..."
mkdir -p data/chroma_db
mkdir -p data/uploads
mkdir -p data/knowledge
mkdir -p logs
log_success "Diretórios criados"

# ======================================================
# 8. Testar importações
# ======================================================
log_info "Testando importações Python..."
python3 -c "
import fastapi
import uvicorn
import chromadb
from groq import Groq
print('✅ Todas as importações OK')
" 2>&1

if [ $? -ne 0 ]; then
    log_error "Erro ao importar dependências!"
    log_info "Verifique o arquivo requirements.txt"
    exit 1
fi

log_success "Importações verificadas"

# ======================================================
# 9. Parar processo existente (se houver)
# ======================================================
log_info "Verificando processos existentes na porta 8000..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_warn "Processo detectado na porta 8000"
    PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    log_info "Parando processo $PID..."
    kill -9 $PID 2>/dev/null || true
    sleep 2
    log_success "Processo anterior parado"
else
    log_info "Nenhum processo rodando na porta 8000"
fi

# ======================================================
# 10. Iniciar o backend
# ======================================================
log_info "Iniciando backend TR4CTION Agent V2..."
echo ""
echo "=========================================="
log_success "Backend será iniciado em: http://0.0.0.0:8000"
log_info "Documentação da API: http://SEU_IP:8000/docs"
log_info "Health Check: http://SEU_IP:8000/health"
echo "=========================================="
echo ""
log_warn "Para rodar em background, use Ctrl+C e execute:"
log_info "  nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > logs/backend.log 2>&1 &"
echo ""
log_warn "Ou configure systemd para inicialização automática"
log_info "  Ver arquivo: tr4ction-backend.service"
echo ""

# Iniciar o servidor
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
