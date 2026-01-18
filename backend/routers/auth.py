"""
Router de Autenticação - Login, Register, Profile
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from db.database import get_db
from services.auth import (
    UserCreate, UserLogin, UserResponse, Token,
    authenticate_user, create_user, create_access_token,
    get_current_user_required, get_current_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES, seed_default_users
)
from db.models import User

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registra um novo usuário (founder por padrão).
    Admin pode criar outros admins via endpoint separado.
    """
    try:
        # Por segurança, não permite criar admin via registro público
        if user_data.role == "admin":
            user_data.role = "founder"
        
        user = create_user(db, user_data)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            company_name=user.company_name,
            is_active=user.is_active,
            created_at=user.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=Token)
async def login(form_data: UserLogin, db: Session = Depends(get_db)):
    """
    Autentica usuário e retorna token JWT.
    """
    user = authenticate_user(db, form_data.email, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Cria token com dados do usuário
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "name": user.name
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "company_name": user.company_name
        }
    )


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login via formulário OAuth2 (para Swagger UI).
    Username é o email.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "name": user.name
        }
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "company_name": user.company_name
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user_required)
):
    """
    Retorna dados do usuário autenticado.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        company_name=current_user.company_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/admin/create-user", response_model=UserResponse)
async def admin_create_user(
    user_data: UserCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Admin cria usuário (pode criar outros admins).
    """
    try:
        user = create_user(db, user_data)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            company_name=user.company_name,
            is_active=user.is_active,
            created_at=user.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Lista todos os usuários (apenas admin).
    """
    users = db.query(User).all()
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            company_name=u.company_name,
            is_active=u.is_active,
            created_at=u.created_at
        )
        for u in users
    ]


@router.post("/seed-defaults")
async def seed_defaults(db: Session = Depends(get_db)):
    """
    Cria usuários padrão (admin e demo).
    Útil para setup inicial.
    """
    try:
        seed_default_users(db)
        return {"status": "ok", "message": "Usuários padrão criados"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ====================================================================
# ENDPOINTS DE ONBOARDING (Aceitar Convite)
# ====================================================================

class AcceptInvitationRequest(BaseModel):
    """Request para aceitar convite"""
    token: str = __import__('pydantic').Field(..., description="Token do convite (recebido via email)")
    password: str = __import__('pydantic').Field(..., description="Senha para criar/atualizar conta")
    name: str = __import__('pydantic').Field(None, description="Nome do usuário (opcional)")


class AcceptInvitationResponse(BaseModel):
    """Response ao aceitar convite"""
    user_id: str
    email: str
    name: str
    organization_id: int
    cycle_id: int
    role: str
    access_token: str
    token_type: str


@router.post("/accept-invitation", response_model=AcceptInvitationResponse)
async def accept_invitation_endpoint(
    request: AcceptInvitationRequest,
    db: Session = Depends(get_db)
):
    """
    Aceita um convite e cria/atualiza o usuário + membership.
    
    Fluxo:
    1. Valida token (existe, não expirou, não foi usado)
    2. Se email já existe → reusar User; senão criar novo
    3. Cria Membership ativa para org/ciclo/role do convite
    4. Marca Invitation como used_at
    5. Retorna JWT para login imediato
    
    Segurança:
    - Token é hashed (SHA256) antes de comparar
    - Senha validada (mínimo 8 chars, maiúscula, minúscula, número, especial)
    - Sem plaintext tokens em logs ou responses
    
    Returns:
        User data + JWT para login imediato
    """
    try:
        from services.onboarding import accept_invitation
        from services.auth import create_access_token
        from datetime import timedelta
        
        # Aceitar convite (cria User + Membership)
        user, membership = accept_invitation(
            db=db,
            token=request.token,
            password=request.password,
            name=request.name,
        )
        
        # Criar JWT
        access_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "role": user.role,
                "name": user.name,
            },
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return AcceptInvitationResponse(
            user_id=user.id,
            email=user.email,
            name=user.name,
            organization_id=membership.organization_id,
            cycle_id=membership.cycle_id,
            role=membership.role,
            access_token=access_token,
            token_type="bearer",
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao aceitar convite: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))