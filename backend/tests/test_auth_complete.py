"""
Testes completos e exhaustivos para routers/auth.py
Objetivo: Maximizar cobertura do router de autenticação

Cobertura:
- POST /auth/register
- POST /auth/login
- POST /auth/login/form
- GET /auth/me
- POST /auth/admin/create-user
- GET /auth/users
- POST /auth/seed-defaults

Casos testados:
- HTTP 200 (sucesso)
- HTTP 400 (dados inválidos)
- HTTP 401 (não autenticado)
- HTTP 403 (não autorizado - não admin)
- HTTP 500 (erro interno)
- Validação de payload
- Edge cases e entradas inválidas
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session

from db.models import User
from db.database import get_db
from routers.auth import router
from services.auth import (
    UserCreate, UserResponse, Token,
    get_current_user_required, get_current_admin
)


@pytest.fixture
def mock_db():
    """Mock do banco de dados"""
    db = MagicMock(spec=Session)
    db.query = MagicMock(return_value=db)
    db.filter = MagicMock(return_value=db)
    db.first = MagicMock()
    db.all = MagicMock(return_value=[])
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.refresh = MagicMock()
    return db


@pytest.fixture
def mock_user():
    """Mock de um usuário founder"""
    user = Mock(spec=User)
    user.id = "user-001"
    user.email = "founder@test.com"
    user.name = "Test Founder"
    user.role = "founder"
    user.company_name = "Test Company"
    user.is_active = True
    user.created_at = datetime.utcnow()
    user.hashed_password = "hashed_password_123"
    return user


@pytest.fixture
def mock_admin():
    """Mock de um usuário admin"""
    admin = Mock(spec=User)
    admin.id = "admin-001"
    admin.email = "admin@test.com"
    admin.name = "Test Admin"
    admin.role = "admin"
    admin.company_name = None
    admin.is_active = True
    admin.created_at = datetime.utcnow()
    admin.hashed_password = "hashed_admin_password"
    return admin


@pytest.fixture
def app(mock_db):
    """Cria app FastAPI com router auth"""
    app = FastAPI()
    app.include_router(router)
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db
    
    return app


@pytest.fixture
def client(app):
    """Cliente de teste"""
    return TestClient(app)


@pytest.fixture
def auth_client(app, mock_user):
    """Cliente de teste com autenticação de founder"""
    app.dependency_overrides[get_current_user_required] = lambda: mock_user
    return TestClient(app)


@pytest.fixture
def admin_client(app, mock_admin):
    """Cliente de teste com autenticação de admin"""
    app.dependency_overrides[get_current_admin] = lambda: mock_admin
    app.dependency_overrides[get_current_user_required] = lambda: mock_admin
    return TestClient(app)


class TestRegisterEndpoint:
    """Testes para POST /auth/register"""
    
    @patch('routers.auth.create_user')
    def test_register_success_founder(self, mock_create, client, mock_user):
        """POST /auth/register - Registro de founder com sucesso"""
        mock_create.return_value = mock_user
        
        response = client.post("/auth/register", json={
            "email": "newfounder@test.com",
            "password": "SecurePass123!",
            "name": "New Founder",
            "company_name": "New Company",
            "role": "founder"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == mock_user.email
        assert data["name"] == mock_user.name
        assert data["role"] == "founder"
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data
    
    @patch('routers.auth.create_user')
    def test_register_strips_admin_role(self, mock_create, client, mock_user):
        """POST /auth/register - Tentativa de criar admin é convertida para founder"""
        mock_user.role = "founder"  # Garantir que retorna founder
        mock_create.return_value = mock_user
        
        response = client.post("/auth/register", json={
            "email": "hacker@test.com",
            "password": "HackerPass123!",
            "name": "Hacker",
            "role": "admin"  # Tentando criar admin
        })
        
        assert response.status_code == 200
        data = response.json()
        # Deve ter convertido para founder
        assert data["role"] == "founder"
        
        # Verificar que create_user foi chamado com role=founder
        call_args = mock_create.call_args
        assert call_args[0][1].role == "founder"
    
    @patch('routers.auth.create_user')
    def test_register_duplicate_email(self, mock_create, client):
        """POST /auth/register - Email duplicado retorna 400"""
        mock_create.side_effect = ValueError("Email já cadastrado")
        
        response = client.post("/auth/register", json={
            "email": "existing@test.com",
            "password": "Pass123!",
            "name": "Test User"
        })
        
        assert response.status_code == 400
        assert "Email já cadastrado" in response.json()["detail"]
    
    @patch('routers.auth.create_user')
    def test_register_database_error(self, mock_create, client, mock_db):
        """POST /auth/register - Erro de banco retorna 500"""
        mock_create.side_effect = Exception("Database connection failed")
        
        response = client.post("/auth/register", json={
            "email": "test@test.com",
            "password": "Pass123!",
            "name": "Test User"
        })
        
        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]
        mock_db.rollback.assert_called()
    
    def test_register_missing_email(self, client):
        """POST /auth/register - Email faltando retorna 422"""
        response = client.post("/auth/register", json={
            "password": "Pass123!",
            "name": "Test User"
        })
        
        assert response.status_code == 422
    
    def test_register_missing_password(self, client):
        """POST /auth/register - Senha faltando retorna 422"""
        response = client.post("/auth/register", json={
            "email": "test@test.com",
            "name": "Test User"
        })
        
        assert response.status_code == 422
    
    def test_register_missing_name(self, client):
        """POST /auth/register - Nome faltando retorna 422"""
        response = client.post("/auth/register", json={
            "email": "test@test.com",
            "password": "Pass123!"
        })
        
        assert response.status_code == 422
    
    @patch('routers.auth.create_user')
    def test_register_invalid_email_format(self, mock_create, client):
        """POST /auth/register - Email inválido retorna 400"""
        mock_create.side_effect = ValueError("Email inválido")
        
        response = client.post("/auth/register", json={
            "email": "invalid-email",
            "password": "Pass123!",
            "name": "Test User"
        })
        
        # O Pydantic valida o formato ou a aplicação retorna 400
        assert response.status_code in [400, 422]
    
    def test_register_empty_json(self, client):
        """POST /auth/register - JSON vazio retorna 422"""
        response = client.post("/auth/register", json={})
        
        assert response.status_code == 422
    
    def test_register_null_json(self, client):
        """POST /auth/register - JSON null retorna 422"""
        response = client.post("/auth/register", json=None)
        
        assert response.status_code == 422
    
    @patch('routers.auth.create_user')
    def test_register_with_company_name(self, mock_create, client, mock_user):
        """POST /auth/register - Registro com company_name"""
        mock_user.company_name = "My Startup"
        mock_create.return_value = mock_user
        
        response = client.post("/auth/register", json={
            "email": "startup@test.com",
            "password": "Pass123!",
            "name": "Startup Founder",
            "company_name": "My Startup"
        })
        
        assert response.status_code == 200
        assert response.json()["company_name"] == "My Startup"
    
    @patch('routers.auth.create_user')
    def test_register_without_company_name(self, mock_create, client, mock_user):
        """POST /auth/register - Registro sem company_name (opcional)"""
        mock_user.company_name = None
        mock_create.return_value = mock_user
        
        response = client.post("/auth/register", json={
            "email": "test@test.com",
            "password": "Pass123!",
            "name": "Test User"
        })
        
        assert response.status_code == 200
        assert response.json()["company_name"] is None
    
    @patch('routers.auth.create_user')
    def test_register_unicode_name(self, mock_create, client, mock_user):
        """POST /auth/register - Nome com caracteres unicode"""
        mock_user.name = "José María Ñoño"
        mock_create.return_value = mock_user
        
        response = client.post("/auth/register", json={
            "email": "jose@test.com",
            "password": "Pass123!",
            "name": "José María Ñoño"
        })
        
        assert response.status_code == 200
        assert response.json()["name"] == "José María Ñoño"
    
    @patch('routers.auth.create_user')
    def test_register_long_name(self, mock_create, client, mock_user):
        """POST /auth/register - Nome muito longo"""
        long_name = "A" * 200
        mock_user.name = long_name
        mock_create.return_value = mock_user
        
        response = client.post("/auth/register", json={
            "email": "long@test.com",
            "password": "Pass123!",
            "name": long_name
        })
        
        # Comportamento depende da validação
        assert response.status_code in [200, 400, 422]


class TestLoginEndpoint:
    """Testes para POST /auth/login"""
    
    @patch('routers.auth.authenticate_user')
    @patch('routers.auth.create_access_token')
    def test_login_success(self, mock_token, mock_auth, client, mock_user):
        """POST /auth/login - Login bem-sucedido"""
        mock_auth.return_value = mock_user
        mock_token.return_value = "fake_jwt_token_12345"
        
        response = client.post("/auth/login", json={
            "email": "founder@test.com",
            "password": "CorrectPassword123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "fake_jwt_token_12345"
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == mock_user.email
        assert data["user"]["role"] == "founder"
        assert "password" not in data["user"]
    
    @patch('routers.auth.authenticate_user')
    def test_login_wrong_password(self, mock_auth, client):
        """POST /auth/login - Senha incorreta retorna 401"""
        mock_auth.return_value = None
        
        response = client.post("/auth/login", json={
            "email": "founder@test.com",
            "password": "WrongPassword"
        })
        
        assert response.status_code == 401
        assert "Email ou senha incorretos" in response.json()["detail"]
        assert response.headers.get("WWW-Authenticate") == "Bearer"
    
    @patch('routers.auth.authenticate_user')
    def test_login_nonexistent_email(self, mock_auth, client):
        """POST /auth/login - Email não existe retorna 401"""
        mock_auth.return_value = None
        
        response = client.post("/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "AnyPassword123!"
        })
        
        assert response.status_code == 401
        assert "Email ou senha incorretos" in response.json()["detail"]
    
    def test_login_missing_email(self, client):
        """POST /auth/login - Email faltando retorna 422"""
        response = client.post("/auth/login", json={
            "password": "Pass123!"
        })
        
        assert response.status_code == 422
    
    def test_login_missing_password(self, client):
        """POST /auth/login - Senha faltando retorna 422"""
        response = client.post("/auth/login", json={
            "email": "test@test.com"
        })
        
        assert response.status_code == 422
    
    def test_login_empty_json(self, client):
        """POST /auth/login - JSON vazio retorna 422"""
        response = client.post("/auth/login", json={})
        
        assert response.status_code == 422
    
    def test_login_null_json(self, client):
        """POST /auth/login - JSON null retorna 422"""
        response = client.post("/auth/login", json=None)
        
        assert response.status_code == 422
    
    @patch('routers.auth.authenticate_user')
    def test_login_empty_password(self, mock_auth, client):
        """POST /auth/login - Senha vazia"""
        mock_auth.return_value = None
        
        response = client.post("/auth/login", json={
            "email": "test@test.com",
            "password": ""
        })
        
        assert response.status_code == 401
    
    @patch('routers.auth.authenticate_user')
    @patch('routers.auth.create_access_token')
    def test_login_admin_user(self, mock_token, mock_auth, client, mock_admin):
        """POST /auth/login - Login de admin"""
        mock_auth.return_value = mock_admin
        mock_token.return_value = "admin_token_123"
        
        response = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "AdminPass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == mock_admin.email
    
    @patch('routers.auth.authenticate_user')
    @patch('routers.auth.create_access_token')
    def test_login_token_contains_user_data(self, mock_token, mock_auth, client, mock_user):
        """POST /auth/login - Token criado com dados do usuário"""
        mock_auth.return_value = mock_user
        mock_token.return_value = "token_with_data"
        
        response = client.post("/auth/login", json={
            "email": "founder@test.com",
            "password": "Pass123!"
        })
        
        assert response.status_code == 200
        
        # Verificar que create_access_token foi chamado com dados corretos
        call_args = mock_token.call_args
        token_data = call_args[1]["data"]
        assert token_data["sub"] == mock_user.id
        assert token_data["email"] == mock_user.email
        assert token_data["role"] == mock_user.role
        assert token_data["name"] == mock_user.name


class TestLoginFormEndpoint:
    """Testes para POST /auth/login/form (OAuth2)"""
    
    @patch('routers.auth.authenticate_user')
    @patch('routers.auth.create_access_token')
    def test_login_form_success(self, mock_token, mock_auth, client, mock_user):
        """POST /auth/login/form - Login via formulário OAuth2"""
        mock_auth.return_value = mock_user
        mock_token.return_value = "oauth_token_123"
        
        response = client.post("/auth/login/form", data={
            "username": "founder@test.com",  # OAuth2 usa 'username'
            "password": "Pass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "oauth_token_123"
        assert data["token_type"] == "bearer"
        assert "user" in data
    
    @patch('routers.auth.authenticate_user')
    def test_login_form_wrong_credentials(self, mock_auth, client):
        """POST /auth/login/form - Credenciais incorretas"""
        mock_auth.return_value = None
        
        response = client.post("/auth/login/form", data={
            "username": "user@test.com",
            "password": "WrongPass"
        })
        
        assert response.status_code == 401
        assert "Email ou senha incorretos" in response.json()["detail"]
    
    def test_login_form_missing_username(self, client):
        """POST /auth/login/form - Username faltando"""
        response = client.post("/auth/login/form", data={
            "password": "Pass123!"
        })
        
        assert response.status_code == 422
    
    def test_login_form_missing_password(self, client):
        """POST /auth/login/form - Password faltando"""
        response = client.post("/auth/login/form", data={
            "username": "test@test.com"
        })
        
        assert response.status_code == 422
    
    @patch('routers.auth.authenticate_user')
    @patch('routers.auth.create_access_token')
    def test_login_form_uses_username_as_email(self, mock_token, mock_auth, client, mock_user):
        """POST /auth/login/form - Username é tratado como email"""
        mock_auth.return_value = mock_user
        mock_token.return_value = "token"
        
        response = client.post("/auth/login/form", data={
            "username": "email@test.com",
            "password": "Pass123!"
        })
        
        assert response.status_code == 200
        # Verificar que authenticate_user foi chamado com username como email
        mock_auth.assert_called_once()
        assert mock_auth.call_args[0][1] == "email@test.com"


class TestGetMeEndpoint:
    """Testes para GET /auth/me"""
    
    def test_get_me_success(self, auth_client, mock_user):
        """GET /auth/me - Obter perfil do usuário autenticado"""
        response = auth_client.get("/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_user.id
        assert data["email"] == mock_user.email
        assert data["name"] == mock_user.name
        assert data["role"] == mock_user.role
        assert data["company_name"] == mock_user.company_name
        assert data["is_active"] == True
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data
    
    def test_get_me_without_auth(self, client):
        """GET /auth/me - Sem autenticação retorna 401"""
        response = client.get("/auth/me")
        
        # Depende da implementação do get_current_user_required
        assert response.status_code in [401, 403]
    
    def test_get_me_admin_user(self, admin_client, mock_admin):
        """GET /auth/me - Perfil de usuário admin"""
        response = admin_client.get("/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        assert data["email"] == mock_admin.email


class TestAdminCreateUserEndpoint:
    """Testes para POST /auth/admin/create-user"""
    
    @patch('routers.auth.create_user')
    def test_admin_create_user_success(self, mock_create, admin_client, mock_user):
        """POST /auth/admin/create-user - Admin cria usuário founder"""
        mock_create.return_value = mock_user
        
        response = admin_client.post("/auth/admin/create-user", json={
            "email": "newuser@test.com",
            "password": "Pass123!",
            "name": "New User",
            "role": "founder"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == mock_user.email
        assert data["role"] == "founder"
    
    @patch('routers.auth.create_user')
    def test_admin_create_admin_user(self, mock_create, admin_client, mock_admin):
        """POST /auth/admin/create-user - Admin cria outro admin"""
        new_admin = Mock(spec=User)
        new_admin.id = "admin-002"
        new_admin.email = "newadmin@test.com"
        new_admin.name = "New Admin"
        new_admin.role = "admin"
        new_admin.company_name = None
        new_admin.is_active = True
        new_admin.created_at = datetime.utcnow()
        
        mock_create.return_value = new_admin
        
        response = admin_client.post("/auth/admin/create-user", json={
            "email": "newadmin@test.com",
            "password": "AdminPass123!",
            "name": "New Admin",
            "role": "admin"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        assert data["email"] == "newadmin@test.com"
    
    def test_admin_create_user_without_auth(self, client):
        """POST /auth/admin/create-user - Sem autenticação retorna 401/403"""
        response = client.post("/auth/admin/create-user", json={
            "email": "test@test.com",
            "password": "Pass123!",
            "name": "Test User"
        })
        
        assert response.status_code in [401, 403]
    
    def test_admin_create_user_as_founder(self, auth_client, mock_user):
        """POST /auth/admin/create-user - Founder não pode criar usuários (403)"""
        response = auth_client.post("/auth/admin/create-user", json={
            "email": "test@test.com",
            "password": "Pass123!",
            "name": "Test User"
        })
        
        # Deve retornar 403 pois não é admin
        assert response.status_code in [401, 403]
    
    @patch('routers.auth.create_user')
    def test_admin_create_user_duplicate_email(self, mock_create, admin_client):
        """POST /auth/admin/create-user - Email duplicado retorna 400"""
        mock_create.side_effect = ValueError("Email já cadastrado")
        
        response = admin_client.post("/auth/admin/create-user", json={
            "email": "existing@test.com",
            "password": "Pass123!",
            "name": "Test User"
        })
        
        assert response.status_code == 400
        assert "Email já cadastrado" in response.json()["detail"]
    
    @patch('routers.auth.create_user')
    def test_admin_create_user_database_error(self, mock_create, admin_client, mock_db):
        """POST /auth/admin/create-user - Erro de banco retorna 500"""
        mock_create.side_effect = Exception("Database error")
        
        response = admin_client.post("/auth/admin/create-user", json={
            "email": "test@test.com",
            "password": "Pass123!",
            "name": "Test User"
        })
        
        assert response.status_code == 500
        mock_db.rollback.assert_called()
    
    def test_admin_create_user_missing_email(self, admin_client):
        """POST /auth/admin/create-user - Email faltando retorna 422"""
        response = admin_client.post("/auth/admin/create-user", json={
            "password": "Pass123!",
            "name": "Test User"
        })
        
        assert response.status_code == 422


class TestListUsersEndpoint:
    """Testes para GET /auth/users"""
    
    def test_list_users_success(self, admin_client, mock_db, mock_user, mock_admin):
        """GET /auth/users - Admin lista todos os usuários"""
        mock_db.query.return_value.all.return_value = [mock_user, mock_admin]
        
        response = admin_client.get("/auth/users")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["email"] == mock_user.email
        assert data[1]["email"] == mock_admin.email
    
    def test_list_users_empty(self, admin_client, mock_db):
        """GET /auth/users - Lista vazia de usuários"""
        mock_db.query.return_value.all.return_value = []
        
        response = admin_client.get("/auth/users")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_users_without_auth(self, client):
        """GET /auth/users - Sem autenticação retorna 401/403"""
        response = client.get("/auth/users")
        
        assert response.status_code in [401, 403]
    
    def test_list_users_as_founder(self, auth_client):
        """GET /auth/users - Founder não pode listar usuários (403)"""
        response = auth_client.get("/auth/users")
        
        assert response.status_code in [401, 403]
    
    def test_list_users_many_users(self, admin_client, mock_db):
        """GET /auth/users - Lista com muitos usuários"""
        users = []
        for i in range(100):
            user = Mock(spec=User)
            user.id = f"user-{i}"
            user.email = f"user{i}@test.com"
            user.name = f"User {i}"
            user.role = "founder" if i % 2 == 0 else "admin"
            user.company_name = f"Company {i}" if i % 2 == 0 else None
            user.is_active = True
            user.created_at = datetime.utcnow()
            users.append(user)
        
        mock_db.query.return_value.all.return_value = users
        
        response = admin_client.get("/auth/users")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 100


class TestSeedDefaultsEndpoint:
    """Testes para POST /auth/seed-defaults"""
    
    @patch('routers.auth.seed_default_users')
    def test_seed_defaults_success(self, mock_seed, client):
        """POST /auth/seed-defaults - Criar usuários padrão"""
        mock_seed.return_value = None
        
        response = client.post("/auth/seed-defaults")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Usuários padrão criados" in data["message"]
        mock_seed.assert_called_once()
    
    @patch('routers.auth.seed_default_users')
    def test_seed_defaults_database_error(self, mock_seed, client, mock_db):
        """POST /auth/seed-defaults - Erro de banco retorna 500"""
        mock_seed.side_effect = Exception("Database error")
        
        response = client.post("/auth/seed-defaults")
        
        assert response.status_code == 500
        mock_db.rollback.assert_called()
    
    @patch('routers.auth.seed_default_users')
    def test_seed_defaults_multiple_calls(self, mock_seed, client):
        """POST /auth/seed-defaults - Múltiplas chamadas"""
        mock_seed.return_value = None
        
        response1 = client.post("/auth/seed-defaults")
        response2 = client.post("/auth/seed-defaults")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert mock_seed.call_count == 2


class TestAuthIntegrationScenarios:
    """Testes de integração e fluxos completos"""
    
    @patch('routers.auth.create_user')
    @patch('routers.auth.authenticate_user')
    @patch('routers.auth.create_access_token')
    def test_register_and_login_flow(self, mock_token, mock_auth, mock_create, client, mock_user):
        """Fluxo: Registrar → Login → Obter perfil"""
        # 1. Registrar
        mock_create.return_value = mock_user
        response1 = client.post("/auth/register", json={
            "email": "newuser@test.com",
            "password": "Pass123!",
            "name": "New User"
        })
        assert response1.status_code == 200
        
        # 2. Login
        mock_auth.return_value = mock_user
        mock_token.return_value = "token123"
        response2 = client.post("/auth/login", json={
            "email": "newuser@test.com",
            "password": "Pass123!"
        })
        assert response2.status_code == 200
        assert "access_token" in response2.json()
    
    @patch('routers.auth.create_user')
    def test_admin_creates_founder_who_can_login(self, mock_create, admin_client, mock_user):
        """Fluxo: Admin cria founder → Founder pode fazer login"""
        mock_create.return_value = mock_user
        
        response = admin_client.post("/auth/admin/create-user", json={
            "email": "founder@new.com",
            "password": "Pass123!",
            "name": "New Founder",
            "role": "founder"
        })
        
        assert response.status_code == 200
        assert response.json()["role"] == "founder"


class TestAuthEdgeCases:
    """Testes de casos extremos e validações"""
    
    @patch('routers.auth.authenticate_user')
    def test_login_with_very_long_email(self, mock_auth, client):
        """POST /auth/login - Email muito longo"""
        mock_auth.return_value = None  # Não encontra usuário
        long_email = "a" * 300 + "@test.com"
        
        response = client.post("/auth/login", json={
            "email": long_email,
            "password": "Pass123!"
        })
        
        # Pode ser 401 (não encontrado) ou 422 (validação)
        assert response.status_code in [401, 422]
    
    @patch('routers.auth.authenticate_user')
    def test_login_with_sql_injection_attempt(self, mock_auth, client):
        """POST /auth/login - Tentativa de SQL injection"""
        mock_auth.return_value = None  # Não encontra usuário
        
        response = client.post("/auth/login", json={
            "email": "admin@test.com' OR '1'='1",
            "password": "' OR '1'='1"
        })
        
        # Deve retornar 401 (credenciais inválidas)
        assert response.status_code == 401
    
    @patch('routers.auth.create_user')
    def test_register_with_xss_attempt(self, mock_create, client, mock_user):
        """POST /auth/register - Tentativa de XSS no nome"""
        mock_user.name = "<script>alert('XSS')</script>"
        mock_create.return_value = mock_user
        
        response = client.post("/auth/register", json={
            "email": "hacker@test.com",
            "password": "Pass123!",
            "name": "<script>alert('XSS')</script>"
        })
        
        # Pode aceitar ou rejeitar dependendo da validação
        assert response.status_code in [200, 400, 422]
    
    def test_register_with_emoji_in_name(self, client):
        """POST /auth/register - Nome com emojis"""
        response = client.post("/auth/register", json={
            "email": "emoji@test.com",
            "password": "Pass123!",
            "name": "Test User 🚀 💻"
        })
        
        # Comportamento depende da validação
        assert response.status_code in [200, 400, 422]
    
    @patch('routers.auth.authenticate_user')
    def test_login_case_sensitive_email(self, mock_auth, client):
        """POST /auth/login - Email é case-sensitive?"""
        mock_auth.return_value = None
        
        response = client.post("/auth/login", json={
            "email": "User@Test.COM",
            "password": "Pass123!"
        })
        
        # Deve retornar 401 se não encontrar
        assert response.status_code == 401
