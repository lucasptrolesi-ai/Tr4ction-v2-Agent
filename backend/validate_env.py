#!/usr/bin/env python
"""
Validador de configuração .env para TR4CTION Agent
Verifica se todas as variáveis necessárias estão configuradas corretamente
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cores para output
class Colors:
    OK = '\033[92m'
    WARN = '\033[93m'
    ERROR = '\033[91m'
    INFO = '\033[94m'
    RESET = '\033[0m'

def log_ok(msg):
    print(f"{Colors.OK}[OK]{Colors.RESET} {msg}")

def log_warn(msg):
    print(f"{Colors.WARN}[WARN]{Colors.RESET} {msg}")

def log_error(msg):
    print(f"{Colors.ERROR}[ERROR]{Colors.RESET} {msg}")

def log_info(msg):
    print(f"{Colors.INFO}[INFO]{Colors.RESET} {msg}")

# Encontrar arquivo .env
backend_dir = Path(__file__).parent.parent / "backend"
env_file = backend_dir / ".env"

print(f"\n{'='*60}")
print(f"TR4CTION Agent - Validador de Configuração")
print(f"{'='*60}\n")

if not env_file.exists():
    log_error(f".env não encontrado em: {env_file}")
    print("\nPara começar, copie o arquivo .env.example:")
    print(f"  cp {env_file.parent}/.env.example {env_file}")
    sys.exit(1)

log_ok(f".env encontrado em: {env_file}")

# Carregar .env
load_dotenv(env_file)

# Configurações necessárias
required_vars = {
    "GROQ_API_KEY": {
        "type": "secret",
        "description": "Chave de API do Groq",
        "optional": False,
        "fallback": "Modo offline"
    },
    "JWT_SECRET_KEY": {
        "type": "secret",
        "description": "Chave secreta para JWT",
        "optional": False,
        "fallback": "Gerada automaticamente"
    },
    "CORS_ORIGINS": {
        "type": "list",
        "description": "Origens CORS permitidas",
        "optional": True,
        "fallback": "Padrão seguro aplicado"
    },
    "EMBEDDING_PROVIDER": {
        "type": "choice",
        "choices": ["huggingface", "local"],
        "description": "Provider de embeddings",
        "optional": True,
        "default": "huggingface",
        "fallback": "Padrão: huggingface"
    },
    "HF_API_TOKEN": {
        "type": "secret",
        "description": "Token da API HuggingFace",
        "optional": True,
        "fallback": "Embeddings local"
    },
    "MAX_UPLOAD_SIZE_MB": {
        "type": "number",
        "description": "Tamanho máximo de upload (MB)",
        "optional": True,
        "default": "50",
        "fallback": "Padrão: 50MB"
    },
    "RATE_LIMIT_REQUESTS": {
        "type": "number",
        "description": "Limite de requisições por janela",
        "optional": True,
        "default": "100",
        "fallback": "Padrão: 100"
    },
}

print("\n1. Validando variáveis de ambiente:\n")

issues = []
warnings = []

for var_name, config in required_vars.items():
    value = os.getenv(var_name)
    
    if value:
        if config["type"] == "secret":
            # Mostrar apenas primeiros/últimos 4 caracteres
            display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            log_ok(f"{var_name} = {display_value}")
        else:
            log_ok(f"{var_name} = {value}")
    else:
        if not config.get("optional", False):
            log_error(f"{var_name} NÃO CONFIGURADO")
            issues.append({
                "var": var_name,
                "reason": config.get("description", "Variável obrigatória"),
                "fallback": config.get("fallback", "Nenhum fallback disponível")
            })
        else:
            default = config.get("default", "N/A")
            log_warn(f"{var_name} não configurado (usando padrão: {default})")
            warnings.append({
                "var": var_name,
                "fallback": config.get("fallback", "Padrão aplicado")
            })

# Relatório
print(f"\n{'='*60}")
print(f"2. Relatório de Validação")
print(f"{'='*60}\n")

if issues:
    print(f"{Colors.ERROR}[PROBLEMAS CRÍTICOS]{Colors.RESET}\n")
    for issue in issues:
        print(f"  • {issue['var']}")
        print(f"    Descrição: {issue['reason']}")
        print(f"    Fallback: {issue['fallback']}\n")

if warnings:
    print(f"{Colors.WARN}[AVISOS]{Colors.RESET}\n")
    for warning in warnings:
        print(f"  • {warning['var']}")
        print(f"    {warning['fallback']}\n")

# Verificações adicionais
print(f"{Colors.INFO}[VERIFICAÇÕES ADICIONAIS]{Colors.RESET}\n")

# Verificar JWT_SECRET_KEY
jwt_secret = os.getenv("JWT_SECRET_KEY")
if jwt_secret:
    if len(jwt_secret) < 32:
        log_warn("JWT_SECRET_KEY é muito curta (mínimo 32 caracteres recomendado)")
    else:
        log_ok("JWT_SECRET_KEY tem comprimento adequado")
else:
    log_warn("JWT_SECRET_KEY não configurada (será gerada automaticamente)")

# Verificar GROQ_API_KEY
groq_key = os.getenv("GROQ_API_KEY")
if groq_key:
    log_ok("GROQ_API_KEY configurada (modo ONLINE)")
else:
    log_warn("GROQ_API_KEY não configurada (modo OFFLINE)")

# Verificar provider
embedding_provider = os.getenv("EMBEDDING_PROVIDER", "huggingface")
if embedding_provider == "huggingface":
    hf_token = os.getenv("HF_API_TOKEN")
    if hf_token:
        log_ok("HuggingFace embedding provider configurado")
    else:
        log_warn("HuggingFace provider sem token (pode afetar performance)")
else:
    log_ok(f"Local embedding provider ({embedding_provider}) configurado")

# Resumo final
print(f"\n{'='*60}")
print(f"RESUMO")
print(f"{'='*60}\n")

if issues:
    print(f"{Colors.ERROR}[ERRO]{Colors.RESET} {len(issues)} problema(s) crítico(s) encontrado(s)")
    print("\nResolva os problemas acima antes de iniciar a aplicação.\n")
    sys.exit(1)
elif warnings:
    print(f"{Colors.WARN}[AVISO]{Colors.RESET} {len(warnings)} aviso(s) encontrado(s)")
    print(f"\n{Colors.OK}[OK]{Colors.RESET} Configuração válida (com fallbacks)\n")
    sys.exit(0)
else:
    print(f"{Colors.OK}[OK]{Colors.RESET} Configuração totalmente válida!\n")
    sys.exit(0)
