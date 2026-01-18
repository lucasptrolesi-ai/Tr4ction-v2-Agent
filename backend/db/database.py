"""
Database configuration
- Usa DATABASE_URL da env quando definida (recomendado em produção)
- Fallback seguro para SQLite em volume persistente (/app/data/tr4ction.db)
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Prioriza variável de ambiente (PostgreSQL/SQLite)
# Em desenvolvimento, usa um banco local
if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    # Verificar se estamos em /app (container) ou no desenvolvimento local
    if os.path.exists("/app/data"):
        DEFAULT_SQLITE_FILE = "/app/data/tr4ction.db"
    else:
        # Desenvolvimento local - criar db na pasta do backend
        db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "data")
        os.makedirs(db_dir, exist_ok=True)
        DEFAULT_SQLITE_FILE = os.path.join(db_dir, "tr4ction.db")
    
    DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_FILE}"

# Configurações específicas para SQLite
is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    echo=False
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para os models
Base = declarative_base()


def get_db():
    """
    Dependency para injetar sessão do banco nos endpoints.
    Uso: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Cria todas as tabelas no banco.
    Chamar no startup da aplicação.
    """
    from . import models  # Importa models para registrar no Base
    Base.metadata.create_all(bind=engine)
    print("✅ [DB] Banco de dados inicializado")
