"""
Database configuration - SQLite para MVP
Migrar para PostgreSQL em produção é simples (só mudar DATABASE_URL)
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Caminho do banco SQLite (relativo ao backend/)
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tr4ction.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Engine com configuração específica para SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Necessário para SQLite com FastAPI
    echo=False  # True para debug SQL
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
