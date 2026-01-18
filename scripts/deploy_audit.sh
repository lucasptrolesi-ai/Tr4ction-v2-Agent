#!/bin/bash
# ============================================================================
# TR4CTION AGENT V2 - PRODUCTION DEPLOYMENT AUDIT SCRIPT
# ============================================================================
# Propósito: Validação rigorosa do ambiente antes do deploy
# Versão: 1.0 (Production-ready)
# Data: 2026-01-14
# ============================================================================

set -e  # Exit on error (fail fast)

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log files
AUDIT_LOG="/tmp/tr4ction_deploy_audit_$(date +%Y%m%d_%H%M%S).log"
ERROR_LOG="/tmp/tr4ction_deploy_errors_$(date +%Y%m%d_%H%M%S).log"

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$AUDIT_LOG"
}

log_ok() {
    echo -e "${GREEN}[✓ OK]${NC} $1" | tee -a "$AUDIT_LOG"
}

log_error() {
    echo -e "${RED}[✗ ERROR]${NC} $1" | tee -a "$ERROR_LOG"
}

log_warn() {
    echo -e "${YELLOW}[⚠ WARN]${NC} $1" | tee -a "$AUDIT_LOG"
}

fail() {
    log_error "$1"
    echo ""
    echo -e "${RED}========== DEPLOY ABORTADO ==========${NC}"
    echo "Erros registrados em: $ERROR_LOG"
    exit 1
}

# ============================================================================
# PASSO 1: AUDITORIA DO SERVIDOR
# ============================================================================

echo -e "\n${BLUE}========== PASSO 1: AUDITORIA DO SERVIDOR ==========${NC}\n"

log_info "Verificando versão do SO..."
if grep -q "Ubuntu 22.04" /etc/os-release 2>/dev/null; then
    log_ok "Ubuntu 22.04 LTS detectado"
else
    log_warn "SO não é Ubuntu 22.04. Verificar compatibilidade."
    cat /etc/os-release | grep PRETTY_NAME
fi

log_info "Verificando espaço em disco..."
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    log_ok "Espaço em disco OK: ${DISK_USAGE}% usado"
else
    fail "Disco quase cheio: ${DISK_USAGE}% usado"
fi

log_info "Verificando permissões do usuário..."
if [ "$(id -u)" -eq 0 ]; then
    log_warn "Rodando como root (deploy recomenda usuário sem privilégio)"
else
    log_ok "Usuário atual: $(whoami)"
fi

log_info "Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    log_ok "Python encontrado: $PYTHON_VERSION"
    
    if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
        log_ok "Python >= 3.10 validado"
    else
        fail "Python >= 3.10 é obrigatório"
    fi
else
    fail "Python3 não instalado"
fi

log_info "Verificando Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    log_ok "Node encontrado: $NODE_VERSION"
    
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        log_ok "NPM encontrado: $NPM_VERSION"
    else
        fail "NPM não instalado"
    fi
else
    fail "Node.js não instalado"
fi

log_info "Verificando Git..."
if command -v git &> /dev/null; then
    log_ok "Git encontrado: $(git --version)"
else
    fail "Git não instalado"
fi

# ============================================================================
# PASSO 2: VALIDAR AMBIENTE PYTHON
# ============================================================================

echo -e "\n${BLUE}========== PASSO 2: ATIVAR E VALIDAR AMBIENTE PYTHON ==========${NC}\n"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
log_info "Diretório do projeto: $PROJECT_ROOT"

if [ ! -f "$PROJECT_ROOT/backend/requirements.txt" ]; then
    fail "requirements.txt não encontrado em $PROJECT_ROOT/backend/"
fi
log_ok "requirements.txt encontrado"

# Procurar venv
VENV_PATH=""
if [ -d "$PROJECT_ROOT/venv" ]; then
    VENV_PATH="$PROJECT_ROOT/venv"
elif [ -d "$PROJECT_ROOT/.venv" ]; then
    VENV_PATH="$PROJECT_ROOT/.venv"
else
    log_warn "venv não encontrado. Criar novo venv..."
    python3 -m venv "$PROJECT_ROOT/venv"
    VENV_PATH="$PROJECT_ROOT/venv"
fi

log_ok "venv localizado: $VENV_PATH"

# Ativar venv
source "$VENV_PATH/bin/activate"
log_ok "venv ativado"

# Validar pip
log_info "Atualizando pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
log_ok "pip, setuptools, wheel atualizados"

# Instalar requirements
log_info "Instalando dependências de requirements.txt..."
if pip install -r "$PROJECT_ROOT/backend/requirements.txt" > /dev/null 2>&1; then
    log_ok "Dependências instaladas com sucesso"
else
    fail "Erro ao instalar dependências. Verificar requirements.txt"
fi

# Validar imports críticos
log_info "Validando imports críticos..."
python3 -c "import fastapi; import sqlalchemy; import openpyxl; import alembic" 2>/dev/null || \
    fail "Erro ao importar dependências críticas"
log_ok "Imports críticos validados"

# ============================================================================
# PASSO 3: CORRIGIR IMPORTS BLOQUEANTES
# ============================================================================

echo -e "\n${BLUE}========== PASSO 3: AUDITAR IMPORTS BLOQUEANTES ==========${NC}\n"

log_info "Verificando backend/routers/founder.py..."
if grep -q "backend.enterprise" "$PROJECT_ROOT/backend/routers/founder.py" 2>/dev/null; then
    log_error "Encontrado import inválido: 'backend.enterprise'"
    log_error "Este import causará ModuleNotFoundError no startup"
    fail "Corrigir imports em founder.py antes de prosseguir"
else
    log_ok "Nenhum import 'backend.enterprise' encontrado"
fi

log_info "Verificando outros imports inválidos..."
if grep -r "from backend\." "$PROJECT_ROOT/backend/routers/" 2>/dev/null | grep -v ".pyc" > /tmp/bad_imports.txt; then
    if [ -s /tmp/bad_imports.txt ]; then
        log_warn "Encontrados imports que começam com 'from backend.':"
        cat /tmp/bad_imports.txt
        log_warn "Revisar e corrigir se necessário"
    else
        log_ok "Nenhum import 'from backend.' encontrado"
    fi
fi

# ============================================================================
# PASSO 4: VALIDAR .env
# ============================================================================

echo -e "\n${BLUE}========== PASSO 4: VALIDAÇÃO RIGOROSA DO .env ==========${NC}\n"

ENV_FILE="$PROJECT_ROOT/backend/.env"

if [ ! -f "$ENV_FILE" ]; then
    fail ".env não encontrado em $PROJECT_ROOT/backend/"
fi
log_ok ".env encontrado"

# Variáveis críticas obrigatórias
CRITICAL_VARS=(
    "DATABASE_URL"
    "TEMPLATE_STORAGE_PATH"
    "DATA_DIR"
    "JWT_SECRET"
    "LLM_PROVIDER"
)

log_info "Verificando variáveis críticas..."
for var in "${CRITICAL_VARS[@]}"; do
    if grep -q "^${var}=" "$ENV_FILE"; then
        VALUE=$(grep "^${var}=" "$ENV_FILE" | cut -d'=' -f2-)
        if [ -z "$VALUE" ] || [ "$VALUE" = '""' ]; then
            fail "$var está vazio em .env"
        fi
        log_ok "$var presente e não-vazio"
    else
        fail "$var não encontrado em .env"
    fi
done

# Verificar LLM_PROVIDER e chave correspondente
LLM_PROVIDER=$(grep "^LLM_PROVIDER=" "$ENV_FILE" | cut -d'=' -f2-)
if [ "$LLM_PROVIDER" = "groq" ]; then
    if grep -q "^GROQ_API_KEY=" "$ENV_FILE"; then
        GROQ_KEY=$(grep "^GROQ_API_KEY=" "$ENV_FILE" | cut -d'=' -f2-)
        if [ -z "$GROQ_KEY" ] || [ "$GROQ_KEY" = '""' ]; then
            fail "GROQ_API_KEY está vazio (LLM_PROVIDER=groq)"
        fi
        log_ok "GROQ_API_KEY configurado"
    else
        fail "GROQ_API_KEY não encontrado (LLM_PROVIDER=groq)"
    fi
elif [ "$LLM_PROVIDER" = "openai" ]; then
    if grep -q "^OPENAI_API_KEY=" "$ENV_FILE"; then
        OPENAI_KEY=$(grep "^OPENAI_API_KEY=" "$ENV_FILE" | cut -d'=' -f2-)
        if [ -z "$OPENAI_KEY" ] || [ "$OPENAI_KEY" = '""' ]; then
            fail "OPENAI_API_KEY está vazio (LLM_PROVIDER=openai)"
        fi
        log_ok "OPENAI_API_KEY configurado"
    else
        fail "OPENAI_API_KEY não encontrado (LLM_PROVIDER=openai)"
    fi
fi

log_ok "Todas as variáveis críticas validadas"

# ============================================================================
# PASSO 5: ALEMBIC MIGRATIONS
# ============================================================================

echo -e "\n${BLUE}========== PASSO 5: ALEMBIC MIGRATIONS ==========${NC}\n"

cd "$PROJECT_ROOT/backend"

log_info "Verificando alembic.ini..."
if [ ! -f "alembic.ini" ]; then
    fail "alembic.ini não encontrado"
fi
log_ok "alembic.ini encontrado"

log_info "Executando: alembic upgrade head"
if alembic upgrade head > /tmp/alembic.log 2>&1; then
    log_ok "Migrations executadas com sucesso"
else
    log_error "Erro ao executar migrations:"
    cat /tmp/alembic.log
    fail "Alembic upgrade falhou"
fi

# Verificar se tabelas foram criadas
log_info "Verificando se tabelas foram criadas..."
python3 << 'EOF'
import sqlite3
import sys

db_path = "data/tr4ction.db"
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('template_definitions', 'fillable_fields')")
    tables = cursor.fetchall()
    
    required_tables = {'template_definitions', 'fillable_fields'}
    found_tables = {table[0] for table in tables}
    
    if required_tables.issubset(found_tables):
        print("✓ Tabelas FCJ criadas com sucesso")
        sys.exit(0)
    else:
        missing = required_tables - found_tables
        print(f"✗ Tabelas faltando: {missing}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Erro ao verificar tabelas: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    fail "Tabelas FCJ não criadas"
fi

# ============================================================================
# PASSO 6: ESTRUTURA DE STORAGE
# ============================================================================

echo -e "\n${BLUE}========== PASSO 6: CRIAR DIRETÓRIOS DE STORAGE ==========${NC}\n"

# Extrair paths do .env
DATA_DIR=$(grep "^DATA_DIR=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"')
TEMPLATE_STORAGE_PATH=$(grep "^TEMPLATE_STORAGE_PATH=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"')

log_info "DATA_DIR: $DATA_DIR"
log_info "TEMPLATE_STORAGE_PATH: $TEMPLATE_STORAGE_PATH"

# Criar diretórios
for dir in "$DATA_DIR" "$TEMPLATE_STORAGE_PATH" "$DATA_DIR/chroma_db" "$DATA_DIR/templates_images" "$DATA_DIR/knowledge" "$DATA_DIR/uploads"; do
    if [ ! -d "$dir" ]; then
        log_info "Criando diretório: $dir"
        mkdir -p "$dir" || fail "Erro ao criar $dir"
    fi
    log_ok "Diretório validado: $dir"
done

# Verificar permissões
log_info "Verificando permissões de escrita..."
for dir in "$DATA_DIR" "$TEMPLATE_STORAGE_PATH"; do
    if [ ! -w "$dir" ]; then
        fail "Sem permissão de escrita em $dir"
    fi
    log_ok "Permissão de escrita OK: $dir"
done

# ============================================================================
# PASSO 7: TESTE DE STARTUP DO BACKEND
# ============================================================================

echo -e "\n${BLUE}========== PASSO 7: TESTE DE STARTUP DO BACKEND ==========${NC}\n"

log_info "Iniciando teste de import (python backend/main.py)..."

cd "$PROJECT_ROOT/backend"

# Timeout de 10 segundos
timeout 10 python -c "
import sys
sys.path.insert(0, '.')
try:
    from main import app
    print('✓ Backend importado com sucesso')
    sys.exit(0)
except Exception as e:
    print(f'✗ Erro ao importar backend: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" > /tmp/backend_import.log 2>&1 || {
    log_error "Erro ao importar backend:"
    cat /tmp/backend_import.log
    fail "Backend não pode ser importado"
}

log_ok "Backend importado com sucesso"

# ============================================================================
# RESULTADO FINAL
# ============================================================================

echo -e "\n${GREEN}========== AUDITORIA CONCLUÍDA COM SUCESSO ==========${NC}\n"

log_ok "Todas as validações passaram!"
echo ""
echo "Próximos passos:"
echo "1. Iniciar backend: cd backend && uvicorn main:app --host 0.0.0.0 --port 8000"
echo "2. Testar endpoint: curl http://localhost:8000/health"
echo "3. Testar FCJ: POST /admin/templates/upload (com arquivo .xlsx)"
echo "4. Iniciar frontend: cd frontend && npm run start"
echo ""
echo "Log de auditoria: $AUDIT_LOG"
echo ""
