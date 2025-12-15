"""
Modelos do banco de dados - SQLAlchemy ORM
"""
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class User(Base):
    """
    Usuário do sistema - Admin ou Founder
    """
    __tablename__ = "users"

    id = Column(String(100), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="founder")  # admin, founder
    company_name = Column(String(255), nullable=True)  # Para founders
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class Trail(Base):
    """
    Trilha/Template - Ex: "Marketing Q1", "Onboarding"
    """
    __tablename__ = "trails"

    id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="active")  # active, draft, archived
    
    # Relacionamentos
    steps = relationship("StepSchema", back_populates="trail", cascade="all, delete-orphan")


class StepSchema(Base):
    """
    Schema de uma etapa - define os campos do formulário
    """
    __tablename__ = "step_schemas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trail_id = Column(String(100), ForeignKey("trails.id"), nullable=False)
    step_id = Column(String(100), nullable=False)
    step_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)  # Ordem de exibição
    schema = Column(JSON, nullable=False)  # Campos do formulário
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    trail = relationship("Trail", back_populates="steps")


class StepAnswer(Base):
    """
    Respostas do founder para uma etapa
    """
    __tablename__ = "step_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trail_id = Column(String(100), nullable=False)
    step_id = Column(String(100), nullable=False)
    user_id = Column(String(100), nullable=False, default="demo-user")
    answers = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserProgress(Base):
    """
    Progresso do usuário em uma trilha
    """
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, default="demo-user")
    trail_id = Column(String(100), nullable=False)
    step_id = Column(String(100), nullable=False)
    is_locked = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    progress_percent = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
