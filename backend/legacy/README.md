# Legacy Files

## database.py

**Status:** ❌ DEPRECATED  
**Substituído por:** `backend/db/database.py` (SQLAlchemy)  
**Data de Deprecação:** 2026-01-01

### Descrição

Este arquivo implementava um "banco de dados" JSON simples para armazenar dados de conhecimento.

**Funcionalidades antigas:**
- `_init_db_if_needed()` - Criava `knowledge.json`
- `load_db()` - Carregava JSON do disco
- `save_db()` - Salvava JSON no disco
- `next_id()` - Gerava IDs sequenciais

### Por que foi deprecated?

O sistema migrou para **SQLAlchemy + SQLite** (`backend/db/database.py`) que oferece:
- ✅ Queries SQL estruturadas
- ✅ Relacionamentos entre tabelas
- ✅ Migrations com Alembic
- ✅ Performance superior
- ✅ Preparado para PostgreSQL

### ⚠️ NÃO USE ESTE ARQUIVO EM CÓDIGO NOVO

Se encontrar imports deste arquivo no código, substitua por:

```python
# ERRADO (antigo):
from database import load_db, save_db

# CORRETO (novo):
from db.database import get_db, SessionLocal
from db.models import User, Trail, Template
```

### Histórico

- **2024-Q4:** Implementação inicial (JSON-based)
- **2025-Q1:** Migração para SQLAlchemy
- **2026-01-01:** Movido para `legacy/` durante production hardening
