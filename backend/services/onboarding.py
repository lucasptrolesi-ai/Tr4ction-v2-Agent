"""
Serviço de Onboarding - Gerenciamento de Convites e Memberships
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from db.models import User, Organization, Cycle, Membership, Invitation
from services.auth import get_password_hash, get_user_by_email
import uuid

logger = logging.getLogger(__name__)

# ======================================================
# CONFIGURAÇÕES
# ======================================================

INVITE_TOKEN_TTL_HOURS = int(__import__('os').getenv('INVITE_TOKEN_TTL_HOURS', '168'))  # 7 dias
INVITE_TOKEN_LENGTH = 32  # bytes

# Roles válidas no sistema
VALID_ROLES = {
    'admin_fcj': 'Admin da FCJ - acesso completo',
    'mentor': 'Mentor de trilhas',
    'founder': 'Founder - acesso a trilhas',
    'coordinator': 'Coordenador - gerenciador de ciclos',
}


# ======================================================
# FUNÇÕES AUXILIARES - SEGURANÇA
# ======================================================

def generate_invite_token() -> str:
    """
    Gera token seguro para convite.
    Usa secrets.token_urlsafe para criptografia.
    """
    return secrets.token_urlsafe(INVITE_TOKEN_LENGTH)


def hash_token(token: str) -> str:
    """
    Gera SHA256 hash do token.
    Nunca salva token em plaintext.
    """
    return hashlib.sha256(token.encode()).hexdigest()


# ======================================================
# CRIAR CONVITE
# ======================================================

def create_invitation(
    db: Session,
    email: str,
    organization_id: int,
    cycle_id: int,
    role: str,
    invited_by_user_id: str,
    invitation_message: Optional[str] = None,
    ttl_hours: Optional[int] = None,
) -> Tuple[Invitation, str]:
    """
    Cria um convite para um usuário ingressar em uma org/ciclo com um role.
    
    Fluxo de segurança:
    1. Valida parâmetros
    2. Gera token aleatório
    3. Salva apenas hash do token
    4. Retorna token (para enviar ao usuário) + objeto Invitation
    
    Args:
        email: Email do usuário a convidar
        organization_id: ID da organização
        cycle_id: ID do ciclo
        role: Role desejado (admin_fcj|mentor|founder|coordinator)
        invited_by_user_id: ID do admin que está convidando
        invitation_message: Mensagem personalizada (opcional)
        ttl_hours: TTL customizado (opcional, padrão do env)
    
    Returns:
        (invitation_obj, plain_token) - Token NUNCA deve ser loggado
    
    Raises:
        ValueError se parâmetros inválidos
    
    Idempotência:
        Se já existe convite PENDING para mesmo email/org/cycle:
        - Opção 1: Retornar id do convite existente
        - Opção 2: Revogar e criar novo
        Implementamos: Retornar existente (mais seguro - evita token spam)
    """
    # 1. Validação
    email = email.lower()
    
    if role not in VALID_ROLES:
        raise ValueError(f"Role inválido: {role}. Válidos: {list(VALID_ROLES.keys())}")
    
    # Verificar organização
    org = db.query(Organization).filter_by(id=organization_id).first()
    if not org:
        raise ValueError(f"Organização {organization_id} não encontrada")
    
    if not org.is_active:
        raise ValueError(f"Organização {organization_id} não está ativa")
    
    # Verificar ciclo
    cycle = db.query(Cycle).filter_by(id=cycle_id, organization_id=organization_id).first()
    if not cycle:
        raise ValueError(f"Ciclo {cycle_id} não encontrado ou não pertence a esta organização")
    
    if cycle.status != 'active':
        raise ValueError(f"Ciclo {cycle.name} não está ativo")
    
    # 2. Verificar se já existe convite PENDING para este email
    existing_pending = db.query(Invitation).filter(
        and_(
            Invitation.email == email,
            Invitation.organization_id == organization_id,
            Invitation.cycle_id == cycle_id,
            Invitation.status == 'pending'
        )
    ).first()
    
    if existing_pending:
        # Verificar se expirou
        if existing_pending.expires_at < datetime.utcnow():
            # Expirou, revogar e criar novo
            existing_pending.status = 'expired'
            db.commit()
        else:
            # Ainda válido - retornar idempotente
            logger.info(
                f"Convite já existe para {email} em org {organization_id}/cycle {cycle_id}. "
                f"Retornando ID existente (idempotente)."
            )
            # Retornar token dummy (não pode ser usado, apenas para logging seguro)
            return existing_pending, "[EXISTING_INVITE_ID_RETURNED]"
    
    # 3. Gerar token e hash
    plain_token = generate_invite_token()
    token_hash = hash_token(plain_token)
    
    # TTL
    if ttl_hours is None:
        ttl_hours = INVITE_TOKEN_TTL_HOURS
    
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    
    # 4. Criar convite
    invitation = Invitation(
        email=email,
        token_hash=token_hash,
        organization_id=organization_id,
        cycle_id=cycle_id,
        role=role,
        status='pending',
        expires_at=expires_at,
        invited_by_user_id=invited_by_user_id,
        invitation_message=invitation_message,
    )
    
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    
    logger.info(
        f"Convite criado para {email} em org_id={organization_id}, "
        f"cycle_id={cycle_id}, role={role}, expires_at={expires_at}"
    )
    
    return invitation, plain_token


# ======================================================
# ACEITAR CONVITE
# ======================================================

def accept_invitation(
    db: Session,
    token: str,
    password: str,
    name: Optional[str] = None,
) -> Tuple[User, Membership]:
    """
    Fluxo de aceitação de convite:
    
    1. Hash do token → encontrar Invitation pending e não expirada
    2. Se expirada → erro claro
    3. Se usada → erro claro
    4. Se email já existe em User → reusar User
       Se NÃO existe → criar User com senha
    5. Criar Membership com role/org/cycle do convite
    6. Marcar Invitation como used_at
    7. Retornar (User, Membership)
    
    Args:
        token: Token plaintext do convite (recebido pelo email)
        password: Senha para criar/atualizar User
        name: Nome do usuário (opcional, usa email se não fornecido)
    
    Returns:
        (user, membership)
    
    Raises:
        ValueError: Se token inválido, expirado, ou já usado
    """
    # 1. Hash do token
    token_hash = hash_token(token)
    
    # 2. Encontrar convite
    invitation = db.query(Invitation).filter_by(token_hash=token_hash).first()
    
    if not invitation:
        raise ValueError("Token de convite inválido ou não encontrado")
    
    # 3. Validar estado do convite
    if invitation.status != 'pending':
        raise ValueError(f"Convite já foi {invitation.status}")
    
    if invitation.expires_at < datetime.utcnow():
        invitation.status = 'expired'
        db.commit()
        raise ValueError("Token de convite expirou")
    
    # 4. Lidar com usuário
    email = invitation.email.lower()
    user = get_user_by_email(db, email)
    
    if user:
        # Usuário já existe
        if not user.is_active:
            user.is_active = True
            db.commit()
        logger.info(f"Usuário {email} já existia, reativando se necessário")
    else:
        # Criar novo usuário
        from services.auth import UserCreate, create_user
        
        user_name = name or email.split('@')[0]
        user_data = UserCreate(
            email=email,
            password=password,
            name=user_name,
            role='founder',  # Role padrão; pode ser override via Membership
            company_name=None,
        )
        user = create_user(db, user_data)
        logger.info(f"Novo usuário criado: {email}")
    
    # 5. Criar Membership
    # Verificar se já existe
    existing_membership = db.query(Membership).filter(
        and_(
            Membership.user_id == user.id,
            Membership.organization_id == invitation.organization_id,
            Membership.cycle_id == invitation.cycle_id,
        )
    ).first()
    
    if existing_membership:
        if existing_membership.status == 'revoked':
            # Reativar
            existing_membership.status = 'active'
            existing_membership.revoked_at = None
            existing_membership.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_membership)
            membership = existing_membership
            logger.info(f"Membership reativado para {email}")
        else:
            # Já ativo
            membership = existing_membership
            logger.info(f"Membership já ativo para {email}")
    else:
        # Criar novo
        membership = Membership(
            user_id=user.id,
            organization_id=invitation.organization_id,
            cycle_id=invitation.cycle_id,
            role=invitation.role,
            status='active',
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)
        logger.info(
            f"Membership criado para {email}, "
            f"org_id={invitation.organization_id}, "
            f"cycle_id={invitation.cycle_id}, "
            f"role={invitation.role}"
        )
    
    # 6. Marcar convite como usado
    invitation.status = 'accepted'
    invitation.used_at = datetime.utcnow()
    db.commit()
    
    return user, membership


# ======================================================
# REVOGAR CONVITE
# ======================================================

def revoke_invitation(db: Session, invitation_id: int) -> Invitation:
    """Revoga um convite pendente"""
    invitation = db.query(Invitation).filter_by(id=invitation_id).first()
    
    if not invitation:
        raise ValueError(f"Convite {invitation_id} não encontrado")
    
    if invitation.status != 'pending':
        raise ValueError(f"Apenas convites PENDING podem ser revogados. Status atual: {invitation.status}")
    
    invitation.status = 'revoked'
    db.commit()
    db.refresh(invitation)
    
    logger.info(f"Convite {invitation_id} revogado")
    return invitation


# ======================================================
# REVOGAR MEMBERSHIP
# ======================================================

def revoke_membership(db: Session, membership_id: int) -> Membership:
    """Revoga acesso de um usuário a uma org/ciclo"""
    membership = db.query(Membership).filter_by(id=membership_id).first()
    
    if not membership:
        raise ValueError(f"Membership {membership_id} não encontrado")
    
    if membership.status == 'revoked':
        raise ValueError("Membership já foi revogado")
    
    membership.status = 'revoked'
    membership.revoked_at = datetime.utcnow()
    db.commit()
    db.refresh(membership)
    
    logger.info(
        f"Membership {membership_id} revogado para user={membership.user_id}, "
        f"org={membership.organization_id}, cycle={membership.cycle_id}"
    )
    return membership


# ======================================================
# VERIFICAR MEMBERSHIP ATIVA
# ======================================================

def get_active_membership(
    db: Session,
    user_id: str,
    organization_id: int,
    cycle_id: int,
) -> Optional[Membership]:
    """
    Busca membership ativa para um usuário em um contexto.
    
    Usado pelos guards para verificar se usuário tem acesso.
    """
    return db.query(Membership).filter(
        and_(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
            Membership.cycle_id == cycle_id,
            Membership.status == 'active',
        )
    ).first()


def get_user_memberships(
    db: Session,
    user_id: str,
    status: Optional[str] = 'active',
) -> List[Membership]:
    """
    Lista memberships de um usuário.
    
    Args:
        user_id: ID do usuário
        status: Filtro de status (None = todos)
    """
    query = db.query(Membership).filter_by(user_id=user_id)
    
    if status:
        query = query.filter_by(status=status)
    
    return query.all()


# ======================================================
# LISTAR CONVITES (ADMIN)
# ======================================================

def list_invitations(
    db: Session,
    organization_id: Optional[int] = None,
    cycle_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Invitation], int]:
    """
    Lista convites com filtros opcionais.
    
    Returns:
        (invitations, total_count)
    """
    query = db.query(Invitation)
    
    if organization_id:
        query = query.filter_by(organization_id=organization_id)
    
    if cycle_id:
        query = query.filter_by(cycle_id=cycle_id)
    
    if status:
        query = query.filter_by(status=status)
    
    total = query.count()
    invitations = query.order_by(Invitation.created_at.desc()).offset(skip).limit(limit).all()
    
    return invitations, total


# ======================================================
# LISTAR MEMBERSHIPS (ADMIN)
# ======================================================

def list_memberships(
    db: Session,
    organization_id: Optional[int] = None,
    cycle_id: Optional[int] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Membership], int]:
    """
    Lista memberships com filtros opcionais.
    
    Returns:
        (memberships, total_count)
    """
    query = db.query(Membership)
    
    if organization_id:
        query = query.filter_by(organization_id=organization_id)
    
    if cycle_id:
        query = query.filter_by(cycle_id=cycle_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if role:
        query = query.filter_by(role=role)
    
    total = query.count()
    memberships = query.order_by(Membership.created_at.desc()).offset(skip).limit(limit).all()
    
    return memberships, total
