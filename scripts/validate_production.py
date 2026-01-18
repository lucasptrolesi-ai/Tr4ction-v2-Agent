#!/usr/bin/env python3
"""
================================================================================
TR4CTION AGENT V2 - PRODUCTION VALIDATION SCRIPT
================================================================================

Propósito: Validação final antes de declarar DEPLOY SUCESSO em produção

Execução: python3 validate_production.py

Saída: Relatório detalhado de validação + GO/NO-GO decision
================================================================================
"""

import os
import sys
import sqlite3
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Tuple, List

# =============================================================================
# CONFIG
# =============================================================================

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
ENV_FILE = BACKEND_DIR / ".env"
DB_FILE = BACKEND_DIR / "data" / "tr4ction.db"

# Cores
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

# =============================================================================
# LOGGING
# =============================================================================

def log_ok(msg: str) -> None:
    print(f"{GREEN}[✓]{NC} {msg}")

def log_error(msg: str) -> None:
    print(f"{RED}[✗]{NC} {msg}")

def log_warn(msg: str) -> None:
    print(f"{YELLOW}[⚠]{NC} {msg}")

def log_info(msg: str) -> None:
    print(f"{BLUE}[ℹ]{NC} {msg}")

def log_section(title: str) -> None:
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}{title:^70}{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")

# =============================================================================
# VALIDADORES
# =============================================================================

class ValidationResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""
        self.details: List[str] = []
    
    def pass_check(self, msg: str = "") -> None:
        self.passed = True
        self.message = msg
        log_ok(self.name)
        if msg:
            log_info(msg)
    
    def fail_check(self, msg: str) -> None:
        self.passed = False
        self.message = msg
        log_error(self.name)
        log_error(f"  Motivo: {msg}")
    
    def add_detail(self, detail: str) -> None:
        self.details.append(detail)

# =============================================================================
# VALIDAÇÕES ESPECÍFICAS
# =============================================================================

def check_env_file() -> ValidationResult:
    """Validar arquivo .env"""
    result = ValidationResult("Arquivo .env existe e está válido")
    
    if not ENV_FILE.exists():
        result.fail_check(f".env não encontrado em {ENV_FILE}")
        return result
    
    critical_vars = {
        "DATABASE_URL": "URL do banco de dados",
        "TEMPLATE_STORAGE_PATH": "Caminho para armazenamento de templates",
        "DATA_DIR": "Diretório de dados",
        "JWT_SECRET": "Chave secreta JWT",
        "LLM_PROVIDER": "Provedor de LLM (groq/openai)",
        "DEBUG_MODE": "Modo debug (deve ser false)"
    }
    
    env_data = {}
    with open(ENV_FILE) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_data[key] = value.strip('"').strip("'")
    
    missing = []
    for var, desc in critical_vars.items():
        if var not in env_data:
            missing.append(f"{var} ({desc})")
        elif not env_data[var]:
            missing.append(f"{var} está vazio ({desc})")
    
    if missing:
        result.fail_check(f"Variáveis faltando ou vazias:\n    " + "\n    ".join(missing))
    else:
        # Validação extra
        if env_data.get("DEBUG_MODE", "").lower() == "true":
            result.fail_check("DEBUG_MODE está TRUE em produção (deve ser FALSE)")
        elif len(env_data.get("JWT_SECRET", "")) < 16:
            result.fail_check("JWT_SECRET é fraco (minimo 16 caracteres)")
        else:
            result.pass_check(f"Todas as {len(critical_vars)} variáveis críticas OK")
            for var in critical_vars.keys():
                result.add_detail(f"{var} = {env_data[var][:20]}...")
    
    return result

def check_database() -> ValidationResult:
    """Validar banco de dados e tabelas"""
    result = ValidationResult("Banco de dados e tabelas FCJ")
    
    if not DB_FILE.exists():
        result.fail_check(f"Banco de dados não encontrado: {DB_FILE}")
        return result
    
    try:
        conn = sqlite3.connect(str(DB_FILE))
        cursor = conn.cursor()
        
        # Verificar tabelas críticas
        required_tables = {'template_definitions', 'fillable_fields'}
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        missing_tables = required_tables - existing_tables
        if missing_tables:
            result.fail_check(f"Tabelas faltando: {missing_tables}")
            return result
        
        # Verificar schema
        for table in required_tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            result.add_detail(f"{table}: {len(columns)} colunas")
        
        # Verificar dados de teste
        cursor.execute("SELECT COUNT(*) FROM template_definitions")
        count = cursor.fetchone()[0]
        result.add_detail(f"Templates armazenados: {count}")
        
        conn.close()
        result.pass_check("Banco de dados e tabelas OK")
        
    except Exception as e:
        result.fail_check(f"Erro ao acessar banco: {e}")
    
    return result

def check_backend_startup() -> ValidationResult:
    """Testar startup do backend"""
    result = ValidationResult("Backend (FastAPI) inicia sem erro")
    
    try:
        os.chdir(BACKEND_DIR)
        output = subprocess.run(
            [sys.executable, "-c", "from main import app; print('OK')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if output.returncode != 0:
            result.fail_check(f"Erro ao importar backend:\n{output.stderr}")
        else:
            result.pass_check("Backend importado com sucesso")
        
    except subprocess.TimeoutExpired:
        result.fail_check("Timeout ao iniciar backend (>10s)")
    except Exception as e:
        result.fail_check(f"Erro ao testar backend: {e}")
    
    return result

def check_storage_permissions() -> ValidationResult:
    """Validar permissões de armazenamento"""
    result = ValidationResult("Permissões de storage e diretórios")
    
    env_data = {}
    with open(ENV_FILE) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_data[key] = value.strip('"').strip("'")
    
    paths_to_check = [
        env_data.get("DATA_DIR"),
        env_data.get("TEMPLATE_STORAGE_PATH"),
        str(BACKEND_DIR / "data" / "chroma_db"),
    ]
    
    errors = []
    for path in paths_to_check:
        if not path:
            continue
        
        path_obj = Path(path)
        
        if not path_obj.exists():
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                result.add_detail(f"Criado: {path}")
            except PermissionError:
                errors.append(f"Sem permissão para criar {path}")
        
        if path_obj.exists() and not os.access(path, os.W_OK):
            errors.append(f"Sem permissão de escrita em {path}")
    
    if errors:
        result.fail_check("Erros de permissão:\n    " + "\n    ".join(errors))
    else:
        result.pass_check(f"Storage e permissões OK")
    
    return result

def check_imports() -> ValidationResult:
    """Verificar imports bloqueantes"""
    result = ValidationResult("Imports bloqueantes (foundation check)")
    
    # Procurar por imports inválidos
    bad_imports = []
    routers_dir = BACKEND_DIR / "routers"
    
    for py_file in routers_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        
        with open(py_file) as f:
            content = f.read()
            if "from backend.enterprise" in content:
                bad_imports.append(f"backend.enterprise em {py_file.name}")
            if "from backend.app" in content:
                bad_imports.append(f"from backend.app em {py_file.name}")
    
    if bad_imports:
        result.fail_check("Imports inválidos encontrados:\n    " + "\n    ".join(bad_imports))
    else:
        result.pass_check("Nenhum import bloqueante detectado")
    
    return result

def check_alembic_version() -> ValidationResult:
    """Verificar versão do Alembic"""
    result = ValidationResult("Alembic migration version")
    
    try:
        os.chdir(BACKEND_DIR)
        output = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if output.returncode != 0:
            result.fail_check("Erro ao verificar Alembic version")
        else:
            version = output.stdout.strip()
            result.add_detail(f"Current revision: {version}")
            result.pass_check("Alembic configurado corretamente")
        
    except Exception as e:
        result.fail_check(f"Erro ao verificar Alembic: {e}")
    
    return result

# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    """Execução principal"""
    
    print(f"\n{BLUE}╔{'═'*68}╗{NC}")
    print(f"{BLUE}║ TR4CTION AGENT V2 - PRODUCTION VALIDATION{' '*24}║{NC}")
    print(f"{BLUE}║ {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^66}║{NC}")
    print(f"{BLUE}╚{'═'*68}╝{NC}\n")
    
    # Array de testes
    tests = [
        check_env_file,
        check_storage_permissions,
        check_imports,
        check_alembic_version,
        check_database,
        check_backend_startup,
    ]
    
    results: List[ValidationResult] = []
    
    # Executar testes
    for i, test_func in enumerate(tests, 1):
        log_section(f"TESTE {i}/{len(tests)}: {test_func.__doc__}")
        result = test_func()
        results.append(result)
        
        for detail in result.details:
            log_info(detail)
    
    # Resultado final
    log_section("RESULTADO FINAL")
    
    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    
    print(f"Testes passados: {passed_count}/{total_count}\n")
    
    for result in results:
        status = f"{GREEN}✓{NC}" if result.passed else f"{RED}✗{NC}"
        print(f"{status} {result.name}")
    
    # Decision
    print()
    if passed_count == total_count:
        print(f"{GREEN}{'='*70}{NC}")
        print(f"{GREEN}{'GO/DEPLOY APROVADO':^70}{NC}")
        print(f"{GREEN}{'='*70}{NC}")
        print(f"\nTodas as {total_count} validações passaram.")
        print("Sistema pronto para produção.\n")
        return 0
    else:
        print(f"{RED}{'='*70}{NC}")
        print(f"{RED}{'NO-GO/DEPLOY REJEITADO':^70}{NC}")
        print(f"{RED}{'='*70}{NC}")
        print(f"\n{passed_count}/{total_count} validações passaram.")
        print(f"{total_count - passed_count} validações falharam.\n")
        print("Corrigir os erros antes de prosseguir com o deploy.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
