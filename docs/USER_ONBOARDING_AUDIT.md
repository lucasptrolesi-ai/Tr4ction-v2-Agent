# AUDITORIA - SISTEMA DE ONBOARDING DE USUÁRIOS FCJ

**Data**: 18 de janeiro de 2026  
**Versão do Sistema**: TR4CTION Agent V2  
**Status**: ✅ Auditoria Fase 0 Completa

---

## 1️⃣ MODELO USER ATUAL

**Arquivo**: `backend/db/models.py` (linhas 11-34)

### Estrutura
```python
class User(Base):
    __tablename__ = "users"
    
    # PK
    id = Column(String(100), primary_key=True)  # UUID string
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Autenticação
    hashed_password = Column(String(255), nullable=False)
    
    # Perfil
    name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)  # Para founders
    
    # Autorização
    role = Column(String(50), nullable=False, default="founder")  # admin | founder
    
    # Status
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Roles Existentes
- **admin**: Administrador (acesso completo, gerenciamento de templates/conhecimento)
- **founder**: Founder (acesso a trilhas educacionais, respostas)

### Observações
- ✅ Email é unique (bom para convites)
- ✅ Senha hasheada com bcrypt (seguro)
- ✅ Sistema de roles simples e extensível
- ⚠️ Sem contexto Organization/Cycle (será necessário adicionar via Membership)
- ⚠️ Sem modelo de convite (será necessário criar)

---

## 2️⃣ AUTENTICAÇÃO JWT

**Arquivo**: `backend/services/auth.py`

### Configuração
```python
SECRET_KEY = get_jwt_secret()  # Via env ou fallback dev
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24h
```

### Funções Chave
- `create_access_token(data, expires_delta)` → gera JWT
- `decode_token(token)` → valida e extrai TokenData
- `verify_password()` / `get_password_hash()` → bcrypt

### Guards Existentes ✅

| Guard | Descrição |
|-------|-----------|
| `get_current_user()` | Retorna User ou None (opcional) |
| `get_current_user_required()` | Exige autenticação (401 se falhar) |
| `get_current_admin()` | Exige role=admin (403 se falhar) |
| `get_current_founder()` | Exige role=founder (403 se falhar) |
| `get_current_user_id()` | Retorna ID ou "demo-user" (fallback) |

### Payload JWT
```json
{
  "sub": "user-id",
  "email": "user@example.com",
  "role": "admin|founder",
  "name": "User Name",
  "exp": 1234567890
}
```

### Observações
- ✅ JWT está bem implementado (exp, HS256, bcrypt)
- ✅ Guards reutilizáveis e seguros
- ✅ Secret via env (production-ready)
- ⚠️ Role-based access é simples (admin/founder only)
- ⚠️ Sem controle granular por Organization/Cycle

---

## 3️⃣ RBAC - ROLES EXISTENTES

**Arquivo**: `backend/services/auth.py` (linhas 79-82), `backend/db/models.py` (linha 24)

### Roles Atuais
1. **admin**
   - Acesso: /admin/* (templates, conhecimento, trilhas)
   - Guard: `get_current_admin()`
   
2. **founder**
   - Acesso: /founder/* (trilhas, respostas)
   - Guard: `get_current_founder()`

### Para Onboarding FCJ Será Necessário
- **admin_fcj** (ou manter "admin" com permissões estendidas)
- **mentor** (novo - para mentores das trails)
- Possivelmente **coordinator** ou similar

### Observações
- ✅ Role está no User model (simples, sem join table)
- ⚠️ Role é string (sem enum - pode gerar inconsistências)
- ⚠️ Sem suporte a múltiplos roles por usuário (solução: Membership vai resolver)
- ⚠️ Sem permissões granulares (é por role apenas)

---

## 4️⃣ ROUTERS ADMIN EXISTENTES

**Arquivo**: `backend/routers/admin.py` (1247 linhas)

### Endpoints Admin Existentes
- `GET /admin/knowledge` - lista docs da base de conhecimento
- `DELETE /admin/knowledge` - remove doc
- `POST /admin/reset-vector-db` - reseta BD vetorial
- `GET /admin/trails` - lista trilhas
- `POST /admin/templates/upload` - upload de template
- `GET /admin/templates/cycle/{cycle}` - lista templates por ciclo
- `PATCH /admin/templates/{key}/status` - atualiza status do template
- `GET /admin/cycles` - lista ciclos
- Múltiplos endpoints de administração de usuários/progresso

### Guard
- Todos usam `Depends(get_current_admin)` ✅

### Observações
- ✅ Rotas bem organizadas com prefixo /admin
- ✅ Guard implementado consistentemente
- ⚠️ Sem rotas de gerenciamento de usuários (criar/atualizar/deletar)
- ⚠️ Sem rotas de convites

---

## 5️⃣ CONVITES / SIGNUP

**Resultado**: ❌ NÃO EXISTE

### O Que Existe
- `POST /auth/register` - Registro aberto (qualquer email pode se registrar)
- `POST /auth/admin/create-user` - Admin cria usuário (sem convite)

### O Que Falta
- ❌ Modelo Invitation
- ❌ Sistema de token expirável
- ❌ Fluxo "convite → aceite → criação de usuário"
- ❌ Revogação de convites

### Arquivo**: `backend/routers/auth.py` (209 linhas)
```python
@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Permite registro aberto - sem convite
    ...

@router.post("/admin/create-user", response_model=UserResponse)
async def admin_create_user(
    user_data: UserCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # Admin pode criar usuário direto
    ...
```

### Observações
- ✅ Endpoints de auth existem e são seguros
- ⚠️ Sem fluxo de convite (será novo modelo)
- ⚠️ Registro aberto pode não ser desejável para FCJ

---

## 6️⃣ ORGANIZATION / CYCLE / WORKSPACE

**Resultado**: ❌ NÃO EXISTEM COMO MODELOS

### O Que Existe
- `cycle` campo em `TemplateDefinition` (Q1, Q2, Q3, etc.) - **apenas string**
- Não há modelo Organization ou equivalente

### O Que Falta
- ❌ Modelo Organization
- ❌ Modelo Cycle (formal)
- ❌ Modelo Membership (association user → org → cycle)
- ❌ Relacionamentos entre User ↔ Organization ↔ Cycle

### Observações
- ⚠️ Cycle é apenas um string em templates
- ⚠️ Multi-tenancy não implementada
- 💡 Será necessário criar Organization + Cycle + Membership como novos modelos

---

## 7️⃣ ESTRUTURA ALEMBIC / MIGRATIONS

**Arquivo**: `backend/alembic.ini`, `backend/alembic/versions/`

### Migrations Existentes
1. `004_fix_field_id_uniqueness.py` (recente)

### Estrutura
```
backend/
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 004_fix_field_id_uniqueness.py
└── db/
    ├── database.py (engine, SessionLocal, Base, init_db)
    └── models.py (declarative Base)
```

### Base
```python
Base = declarative_base()  # em backend/db/database.py
```

### Observações
- ✅ Alembic configurado
- ✅ SQLite com suporte a migrations
- ✅ Base e engine prontos
- ⚠️ Poucas migrations existentes (sistema novo)
- ✅ Novas migrations serão simples de adicionar

---

## 8️⃣ TESTES EXISTENTES

**Arquivo**: `backend/tests/`

### Testes de Auth ✅
- `test_auth.py` - Testes básicos de JWT
- `test_auth_complete.py` - Suite completa
- `test_security_audit_fixes.py` - Segurança

### Testes de Admin
- `test_admin_router.py` - Endpoints admin

### Outros
- `test_trail_hardening.py` - 30 casos (rodar com `pytest backend/tests/test_trail_hardening.py -v`)
- `test_production_hardening.py` - Testes de produção

### Como Rodar
```bash
# Todos os testes
pytest backend/tests/ -v

# Auth apenas
pytest backend/tests/test_auth*.py -v

# Com cobertura
pytest --cov=backend backend/tests/ -v
```

### Observações
- ✅ Testes de auth existem
- ✅ Infraestrutura pytest funcionando
- ⚠️ Será necessário adicionar testes para Invitation/Membership

---

## 📊 RESUMO DA AUDITORIA

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **User Model** | ✅ Existe | Email unique, role (admin/founder), senha hasheada |
| **JWT Auth** | ✅ Completo | HS256, bcrypt, guards reutilizáveis |
| **RBAC** | ⚠️ Simples | 2 roles; sem granularidade; sem múltiplos roles |
| **Admin Routers** | ✅ Existe | Bem organizados, guard consistente |
| **Convites** | ❌ Não existe | Necessário criar modelo + endpoints |
| **Organization** | ❌ Não existe | Necessário criar modelo |
| **Cycle** | ⚠️ Parcial | Existe como string em templates; necessário formalizar |
| **Membership** | ❌ Não existe | Necessário criar (associação user ↔ org ↔ cycle ↔ role) |
| **Migrations** | ✅ Estrutura OK | Alembic pronto; poucas migrations existentes |
| **Testes** | ✅ Infraestrutura OK | test_auth.py, conftest.py, pytest configurado |

---

## 🎯 DECISÕES DE DESIGN

### 1. Reutilizar User Existente
**Decisão**: ✅ SIM - Manter User como está, adicionar Membership
**Motivo**: 
- User já está em produção
- Adicionar Organization/Cycle via tabela separada (Membership)
- Não quebrar autenticação existente

### 2. Estender Roles
**Decisão**: Adicionar `ADMIN_FCJ` e `MENTOR` como novos roles
**Motivo**:
- Manter compatibilidade com `admin` e `founder`
- Role ainda é string em User, mas pode ter lógica em Membership

### 3. Novo Modelo: Membership
**Decisão**: ✅ SIM - Tabela `memberships(user_id, org_id, cycle_id, role, status)`
**Motivo**:
- Suportar múltiplas organizações por usuário
- Contexto ciclo (Q1, Q2, etc.)
- Role pode ser diferente por contexto

### 4. Modelo Invitation
**Decisão**: ✅ SIM - Criar `Invitation(email, token_hash, org_id, cycle_id, role, status)`
**Motivo**:
- Token expirável
- Auditoria de quem convidou
- Fluxo "aceitar convite → criar membership"

### 5. OAuth2 / JWT
**Decisão**: Manter JWT existente
**Motivo**: Já funciona bem; adicionar verificação de Membership nos guards

---

## 📝 LISTA DE ARQUIVOS PARA MODIFICAR/CRIAR

### ✅ Modificar
- `backend/db/models.py` - Adicionar Organization, Cycle, Membership, Invitation
- `backend/services/auth.py` - Adicionar verificação de Membership nos guards
- `backend/routers/admin.py` - Adicionar endpoints de invitation
- `backend/routers/auth.py` - Adicionar endpoint /auth/accept-invitation

### 🆕 Criar
- `backend/app/models/organization.py` - Model Organization
- `backend/app/models/cycle.py` - Model Cycle (formal)
- `backend/app/models/membership.py` - Model Membership
- `backend/app/models/invitation.py` - Model Invitation
- `backend/alembic/versions/005_create_onboarding_tables.py` - Migration
- `backend/services/onboarding.py` - Funções de convite/acceptance
- `backend/tests/test_onboarding.py` - Testes de convite e membership
- `docs/USER_ONBOARDING.md` - Documentação do fluxo

---

## ⚠️ RISCOS IDENTIFICADOS

### Risco 1: Ciclo Referência
**Descrição**: Cycle é string em TemplateDefinition, mas será modelo formal em Membership
**Mitigação**: Criar migration que relaciona cycles ao novo modelo; manter string legacy

### Risco 2: Role Duplicada
**Descrição**: Role existe em User E em Membership
**Mitigação**: Clarificar preferência (Membership é autoritário); User.role é legacy

### Risco 3: Email Único
**Descrição**: User.email é unique, mas Invitation também refere email
**Mitigação**: Garantir que uma Invitation para um email pendente não conflita com User existente

### Risco 4: Token Vazado
**Descrição**: Se token de convite em plaintext em logs
**Mitigação**: Nunca logar token; logar apenas token_hash

### Risco 5: Colisão de Rota
**Descrição**: /admin/invitations pode conflitar com rotas existentes
**Mitigação**: Verificar com grep antes de implementar

### Risco 6: Downtime de Migration
**Descrição**: Migration destrutiva poderia quebrar dados
**Mitigação**: Migrations serão aditivas (criar tabelas, não deletar)

---

## ✅ RECOMENDAÇÕES PARA PRÓXIMA FASE

1. **Fase 1 - Modelos**: Criar Organization, Cycle, Membership, Invitation em novo arquivo (models)
2. **Fase 2 - Migrations**: Criar migration 005_create_onboarding_tables.py
3. **Fase 3 - Services**: Implementar lógica de convite e acceptance em services/onboarding.py
4. **Fase 4 - Routers**: 
   - POST /admin/invitations (criar convite)
   - GET /admin/invitations (listar convites)
   - PATCH /admin/invitations/{id}/revoke (revogar)
   - POST /auth/accept-invitation (aceitar e criar membership)
5. **Fase 5 - Guards**: Adicionar `get_current_membership()` que verifica Membership ativa
6. **Fase 6 - Testes**: Suite completa de testes de convite, acceptance, revogação
7. **Fase 7 - Docs**: Atualizar docs/USER_ONBOARDING.md com fluxo, exemplos curl

---

## 🚀 PRÓXIMOS PASSOS

**✅ Auditoria Completa**

**Aguardando**:
1. Aprovação desta auditoria
2. Decisão sobre nomes de campos (ex: `org_id` vs `organization_id`)
3. Decisão sobre roles adicionais (MENTOR, COORDINATOR, etc.)
4. TTL padrão para convites (ex: 7 dias)

**Pronto para Implementação**: Todas as 7 fases estão planejadas

---

**Status**: 🟢 PRONTO PARA FASE 1 (Modelos de Dados)

