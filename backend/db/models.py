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
    __table_args__ = {"extend_existing": True}

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
    __table_args__ = {"extend_existing": True}

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
    __table_args__ = {"extend_existing": True}

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
    __table_args__ = {"extend_existing": True}

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
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, default="demo-user")
    trail_id = Column(String(100), nullable=False)
    step_id = Column(String(100), nullable=False)
    is_locked = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    progress_percent = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TemplateDefinition(Base):
    """
    Definição de template Excel - gerado dinamicamente por admin
    Suporta múltiplos cycles (Q1, Q2, Q3, Q4, etc.)
    """
    __tablename__ = "template_definitions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    cycle = Column(String(50), nullable=False, index=True)  # Q1, Q2, Q3, Q4, etc.
    template_key = Column(String(255), nullable=False, index=True)  # cronograma, persona_01, etc.
    sheet_name = Column(String(255), nullable=False)  # Nome original da sheet no Excel
    schema_path = Column(String(500), nullable=False)  # backend/templates/generated/{cycle}/{template_key}.json
    image_path = Column(String(500), nullable=False)  # frontend/public/templates/{cycle}/{template_key}.png
    status = Column(String(50), default="active", index=True)  # active, inactive, archived
    description = Column(Text, nullable=True)
    field_count = Column(Integer, default=0)  # Número de campos editáveis detectados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadados do arquivo fonte
    source_file = Column(String(500), nullable=True)  # Path do arquivo Excel original
    ingestion_report = Column(Text, nullable=True)  # Relatório de warnings/errors durante ingestão

# ====================================================================
# MODELOS DE ONBOARDING (Fase 1 - Sistema de Convites de Usuários)
# ====================================================================

class Organization(Base):
    """
    Organização - FCJ, VentureBuilder, Startup ou outra entidade
    
    Suporta multi-tenancy: um usuário pode estar em múltiplas orgs
    via a tabela Membership.
    """
    __tablename__ = "organizations"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False, default="fcj")  # fcj|venture_builder|startup
    description = Column(Text, nullable=True)
    
    # Metadados
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    memberships = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="organization", cascade="all, delete-orphan")
    cycles = relationship("Cycle", back_populates="organization", cascade="all, delete-orphan")


class Cycle(Base):
    """
    Ciclo de execução - Q1, Q2, Q3, Q4, etc.
    
    Cada ciclo pertence a uma organização.
    Um usuário pode estar em múltiplos ciclos de uma org.
    """
    __tablename__ = "cycles"
    __table_args__ = (
        {"extend_existing": True},
        # Garantir que não haja ciclos duplicados por org
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # Q1, Q2, Q1-2026, etc.
    status = Column(String(50), nullable=False, default="active", index=True)  # active|closed|archived
    description = Column(Text, nullable=True)
    
    # Datas
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    organization = relationship("Organization", back_populates="cycles")
    memberships = relationship("Membership", back_populates="cycle", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="cycle", cascade="all, delete-orphan")


class Membership(Base):
    """
    Associação user ↔ organization ↔ cycle ↔ role (CHAVE)
    
    Define o acesso de um usuário em um contexto específico.
    Um usuário pode ter múltiplas memberships (diferentes orgs, ciclos, roles).
    
    Exemplo:
    - user_id=123, org_id=1, cycle_id=1, role=FOUNDER
    - user_id=123, org_id=2, cycle_id=2, role=MENTOR
    """
    __tablename__ = "memberships"
    __table_args__ = (
        {"extend_existing": True},
        # Garantir que não haja duplicação
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id"), nullable=False, index=True)
    
    # Role neste contexto (pode ser diferente de User.role)
    # ADMIN_FCJ | MENTOR | FOUNDER | COORDINATOR
    role = Column(String(50), nullable=False, default="founder")
    
    # Status
    status = Column(String(50), nullable=False, default="active", index=True)  # active|invited|revoked|suspended
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relacionamentos
    user = relationship("User", foreign_keys=[user_id])
    organization = relationship("Organization", back_populates="memberships")
    cycle = relationship("Cycle", back_populates="memberships")


class Invitation(Base):
    """
    Convite para um usuário ingressar em uma org/ciclo com um role específico
    
    Fluxo:
    1. Admin cria convite (email, org, ciclo, role)
    2. Gera token (salva apenas hash)
    3. Convida (via email com link)
    4. Usuário aceita + define senha
    5. Cria User + Membership com status=active
    6. Marca Invitation como used_at
    
    Segurança:
    - Token é random (secrets.token_urlsafe)
    - Salva apenas sha256(token)
    - Expire_at para invalidar convites antigos
    - used_at para rastrear aceitação
    """
    __tablename__ = "invitations"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identificação do convite
    email = Column(String(255), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)  # sha256 hex
    
    # Contexto
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="founder")  # ADMIN_FCJ|MENTOR|FOUNDER
    
    # Status e timestamps
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending|accepted|expired|revoked
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # Token invalida após esta data
    used_at = Column(DateTime, nullable=True)  # Quando foi aceito
    
    # Auditoria
    invited_by_user_id = Column(String(100), ForeignKey("users.id"), nullable=True)  # Quem convidou
    invitation_message = Column(Text, nullable=True)  # Mensagem personalizada do convite
    
    # Relacionamentos
    organization = relationship("Organization", back_populates="invitations")
    cycle = relationship("Cycle", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])