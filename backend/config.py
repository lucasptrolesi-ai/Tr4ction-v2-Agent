import os
import logging
from dotenv import load_dotenv

# Setup logger for config module
logger = logging.getLogger(__name__)

# =============================================================================
# 🔹 DETECTA SE ESTAMOS EM MODO DE TESTE (PYTEST)
# =============================================================================

IS_TEST_MODE = (
    "PYTEST_CURRENT_TEST" in os.environ
    or os.getenv("TESTING") == "1"
)

# =============================================================================
# 🔹 BASE DO SISTEMA
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

# Carrega o .env do backend
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
    logger.info(f".env loaded from: {ENV_PATH}")
else:
    logger.warning(f".env not found at: {ENV_PATH}")
    logger.warning("Backend started with system environment variables")

# =============================================================================
# 🔹 FUNÇÃO SEGURA PARA CAPTURAR VARIÁVEIS DO .env
# =============================================================================

def get_env(key: str, default=None, required=False):
    """
    Lê variáveis de ambiente com fallback seguro.
    """
    value = os.getenv(key)

    if value is None or value.strip() == "":
        if required:
            raise ValueError(f"❌ ERRO: Variável obrigatória '{key}' não encontrada no .env")
        return default

    return value.strip()

# =============================================================================
# 🔹 DIRETÓRIOS DO SISTEMA
# =============================================================================

DATA_DIR = os.path.join(BASE_DIR, "data")
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "knowledge")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
CHROMA_DB_DIR = get_env("CHROMA_DB_DIR", os.path.join(DATA_DIR, "chroma_db"))

# Garante que todos existam
for path in [DATA_DIR, KNOWLEDGE_DIR, UPLOADS_DIR, CHROMA_DB_DIR]:
    os.makedirs(path, exist_ok=True)

# =============================================================================
# 🔹 CONFIGURAÇÃO DE PROVEDORES (GROQ / OPENAI / OFFLINE)
# =============================================================================

# GROQ
GROQ_API_KEY = get_env("GROQ_API_KEY")
GROQ_MODEL = get_env("GROQ_MODEL", "llama3-70b-versatile")

# OPENAI
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
OPENAI_MODEL = get_env("OPENAI_MODEL", "gpt-4.1-mini")

# Provider ativo
if GROQ_API_KEY:
    LLM_PROVIDER = "groq"
    ACTIVE_MODEL = GROQ_MODEL

elif OPENAI_API_KEY:
    LLM_PROVIDER = "openai"
    ACTIVE_MODEL = OPENAI_MODEL

else:
    LLM_PROVIDER = "offline"
    ACTIVE_MODEL = "mock"
    logger.warning("No API KEY found. Running in OFFLINE mode (mock)")

logger.info(f"Active LLM provider: {LLM_PROVIDER}")
logger.info(f"Active model: {ACTIVE_MODEL}")

# =============================================================================
# 🔹 MODO OFFLINE REFORÇADO (usado em produção sem API Key e no Docker)
# =============================================================================

IS_OFFLINE = (LLM_PROVIDER == "offline")

if IS_TEST_MODE:
    logger.info("TEST mode activated - external APIs disabled")
elif IS_OFFLINE:
    logger.info("OFFLINE mode - no external APIs will be used")
else:
    logger.info(f"ONLINE mode using provider: {LLM_PROVIDER}")

# =============================================================================
# 🔹 CONFIGURAÇÕES GERAIS DO APP
# =============================================================================

APP_NAME = "TR4CTION Agent Backend"
APP_VERSION = "2.0.0"
DEBUG_MODE = get_env("DEBUG_MODE", "false").lower() == "true"

print(f"🔧 [CONFIG] Debug: {DEBUG_MODE}")
print(f"📁 [CONFIG] Diretório de conhecimento: {KNOWLEDGE_DIR}")
print(f"📁 [CONFIG] Diretório de uploads: {UPLOADS_DIR}")
print(f"📁 [CONFIG] Diretório do ChromaDB: {CHROMA_DB_DIR}")
