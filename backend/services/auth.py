"""
Serviço de Autenticação - JWT + Password Hashing
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
import os
import uuid
import secrets

from db.database import get_db
from db.models import User

# ======================================================
# Configurações JWT SEGURAS (via env)
# ======================================================
# Stable dev secret - safe to commit, only for local development
_DEV_STABLE_SECRET = "tr4ction-dev-secret-DO-NOT-USE-IN-PRODUCTION-f8e3d2c1b0a9"

def get_jwt_secret() -> str:
    """
    Obtém JWT secret de forma segura.
    Em produção, DEVE ser definido via variável de ambiente.
    
    Development: Uses stable secret (tokens persist across restarts)
    Production: Requires strong secret, fails if not configured
    """
    secret = os.getenv("JWT_SECRET_KEY")
    
    if not secret or secret == "tr4ction-change-this-in-production-openssl-rand-hex-32":
        # Production: Fail fast with clear error
        if os.getenv("ENVIRONMENT") == "production":
            raise ValueError(
                "❌ CRITICAL: JWT_SECRET_KEY not configured in production! "
                "Generate with: openssl rand -hex 32"
            )
        # Development: Use stable secret for better DX (tokens don't expire on restart)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "Using default dev JWT secret. Set JWT_SECRET_KEY in .env for production!"
        )
        return _DEV_STABLE_SECRET
    
    return secret

SECRET_KEY = get_jwt_secret()
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24h default

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ======================================================
# Schemas Pydantic
# ======================================================

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    role: str = "founder"
    company_name: Optional[str] = None
    
    @validator('password')
    def validate_password_strength(cls, v):
        """
        Valida força da senha segundo padrões de segurança.
        
        Requisitos:
        - Mínimo 8 caracteres
        - Pelo menos 1 letra maiúscula
        - Pelo menos 1 letra minúscula
        - Pelo menos 1 número
        - Pelo menos 1 caractere especial
        """
        import re
        
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r'[0-9]', v):
            raise ValueError("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/]', v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*...)")
        
        return v
    
    @validator('email')
    def validate_email_format(cls, v):
        """Valida formato de email"""
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format")
        return v.lower()


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    company_name: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ======================================================
# Funções de Password
# ======================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gera hash da senha"""
    return pwd_context.hash(password)


# ======================================================
# Funções de Token JWT
# ======================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria token JWT"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decodifica e valida token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        if user_id is None:
            return None
            
        return TokenData(user_id=user_id, email=email, role=role)
    except JWTError:
        return None


# ======================================================
# Funções de Usuário
# ======================================================

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca usuário por email"""
    return db.query(User).filter(User.email == email.lower()).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Busca usuário por ID"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    """Cria novo usuário"""
    # Verifica se email já existe
    existing = get_user_by_email(db, user_data.email)
    if existing:
        raise ValueError("Email já cadastrado")
    
    # Gera ID único
    user_id = str(uuid.uuid4())
    
    # Cria usuário
    user = User(
        id=user_id,
        email=user_data.email.lower(),
        hashed_password=get_password_hash(user_data.password),
        name=user_data.name,
        role=user_data.role,
        company_name=user_data.company_name,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Autentica usuário por email e senha"""
    user = get_user_by_email(db, email)
    
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    
    # Atualiza último login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


# ======================================================
# Dependencies de Autenticação
# ======================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency que retorna o usuário atual baseado no token.
    Retorna None se não autenticado (para rotas opcionais).
    """
    if not token:
        return None
    
    token_data = decode_token(token)
    if not token_data:
        return None
    
    user = get_user_by_id(db, token_data.user_id)
    return user


async def get_current_user_required(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency que EXIGE usuário autenticado.
    Lança exceção 401 se não autenticado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    token_data = decode_token(token)
    if not token_data:
        raise credentials_exception
    
    user = get_user_by_id(db, token_data.user_id)
    if not user:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado"
        )
    
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user_required)
) -> User:
    """
    Dependency que exige usuário com role 'admin'.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado - apenas administradores"
        )
    return current_user


async def get_current_founder(
    current_user: User = Depends(get_current_user_required)
) -> User:
    """
    Dependency que exige usuário com role 'founder'.
    """
    if current_user.role != "founder":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado - apenas founders"
        )
    return current_user


def get_current_user_id(current_user: Optional[User] = Depends(get_current_user)) -> str:
    """
    Retorna o ID do usuário atual ou 'demo-user' se não autenticado.
    Útil para manter compatibilidade com código existente.
    """
    if current_user:
        return current_user.id
    return "demo-user"


# ======================================================
# Seed de Usuários Padrão
# ======================================================

def seed_default_users(db: Session):
    """Cria usuários padrão se não existirem"""
    
    # Admin padrão
    admin_email = "admin@tr4ction.com"
    if not get_user_by_email(db, admin_email):
        admin = User(
            id="admin-default",
            email=admin_email,
            hashed_password=get_password_hash("admin123"),
            name="Administrador TR4CTION",
            role="admin",
            is_active=True
        )
        db.add(admin)
        print(f"✓ Admin criado: {admin_email} / admin123")
    
    # Founder demo
    founder_email = "demo@tr4ction.com"
    if not get_user_by_email(db, founder_email):
        founder = User(
            id="demo-user",  # Mantém compatibilidade com dados existentes
            email=founder_email,
            hashed_password=get_password_hash("demo123"),
            name="Demo Founder",
            role="founder",
            company_name="Demo Startup",
            is_active=True
        )
        db.add(founder)
        print(f"✓ Founder criado: {founder_email} / demo123")
    
    db.commit()
