# ===============================
#   DOCKERFILE - TR4CTION AGENT
#   Produção + Desenvolvimento
# ===============================
# 📌 NOTA: Com EMBEDDING_PROVIDER=huggingface, esta imagem
# consome ~300-400MB RAM (ideal para EC2 t3.micro)
# Se usar EMBEDDING_PROVIDER=local, consome ~600MB+

FROM python:3.11-slim as base

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependências do sistema para compilar pacotes Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ===============================
#   STAGE: Dependencies
# ===============================
FROM base as dependencies

WORKDIR /app

# Copia requirements primeiro (cache layer)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# ===============================
#   STAGE: Production
# ===============================
FROM dependencies as production

WORKDIR /app

# Copia código da aplicação
COPY . .

# Cria diretórios necessários (dentro de /app/data)
RUN mkdir -p /app/data/knowledge \
             /app/data/uploads \
             /app/data/chroma_db \
             /app/data/templates_source \
             /app/data/templates_images \
             /app/logs

# Cria usuário não-root para segurança
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expõe porta
EXPOSE 8000

# Health check (mais tempo no start para inicialização)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de produção (Gunicorn + Uvicorn workers)
# NOTA: 1 worker para t3.micro (1GB RAM)
CMD ["gunicorn", "main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "1", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

# ===============================
#   STAGE: Development
# ===============================
FROM dependencies as development

WORKDIR /app

# Copia código
COPY . .

# Cria diretórios
RUN mkdir -p /app/data/knowledge \
             /app/data/uploads \
             /app/data/chroma_db

# Expõe porta
EXPOSE 8000

# Dev: Uvicorn com reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
