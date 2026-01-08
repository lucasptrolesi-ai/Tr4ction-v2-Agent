"""
📋 ENTERPRISE ARCHITECTURE DOCUMENTATION

TR4CTION Agent V2 - Enterprise-Grade Product Architecture
=========================================================

Esta documentação descreve a camada institucional do TR4CTION Agent,
implementada como extensão 100% compatível com o sistema atual.

## 📐 Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js/Vercel)               │
│         (Consome payloads com cognitive_signals)           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    API REST FastAPI
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                  ENTERPRISE LAYER (NOVO)                   │
│  8 Subsistemas independentes, opcionais, controlados por   │
│  feature flags em backend/enterprise/config.py             │
└──────┬──────────────────────────────────────────────────────┘
       │
       ├─ 🔍 Decision Ledger       (decision_ledger/)
       ├─ 🛡️  Method Governance     (governance/)
       ├─ ⚠️  Risk Detection        (risk_engine/)
       ├─ 💭 Cognitive Memory       (cognitive_memory/)
       ├─ 🎭 Template Engine       (template_engine/)
       ├─ 📝 AI Audit              (ai_audit/)
       ├─ 🧠 Cognitive Signals     (cognitive_signals/)
       └─ 📊 Method Registry       (method_registry/)
       │
┌──────┴──────────────────────────────────────────────────────┐
│              SISTEMA ATUAL (INTACTO + COMPATÍVEL)          │
│  ✓ FastAPI Backend         (routers/, services/)           │
│  ✓ SQLite + ChromaDB       (db/, data/)                    │
│  ✓ Template Registry       (services/template_*.py)        │
│  ✓ AI Mentor Chat          (chat, usecases/)               │
│  ✓ Authentication/Auth     (auth.py, security.py)          │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Feature Flags (CONTROLE TOTAL)

Arquivo: `backend/enterprise/.env.enterprise`

```yaml
ENTERPRISE_DECISION_LEDGER=false        # Rastreabilidade de decisões
ENTERPRISE_METHOD_GOVERNANCE=false      # Validação de método
ENTERPRISE_RISK_ENGINE=false            # Detecção de risco
ENTERPRISE_TEMPLATE_ENGINE=false        # Orquestração dinâmica
ENTERPRISE_COGNITIVE_MEMORY=false       # Persistência de contexto
ENTERPRISE_AI_AUDIT=false               # Compliance de IA
ENTERPRISE_COGNITIVE_SIGNALS=false      # Sinais para Frontend
ENTERPRISE_VERTICALIZATION=false        # Suporte a múltiplas verticais
```

**IMPORTANTE**: Tudo começa como `false`. Ativar incrementalmente em produção.

---

## 📦 SUBSISTEMAS (8 MÓDULOS)

### 1️⃣ Decision Ledger (Event Sourcing Leve)

**Objetivo**: Rastreabilidade completa de cada decisão do founder.

**O que registra**:
- Quem decidiu (user_id, email)
- O quê (campo, valor, versão anterior)
- Quando (timestamp exato)
- Por quê (reasoning)
- Contexto (templates relacionados)
- Consequências esperadas vs. reais (após 30 dias)

**Localização**: `backend/enterprise/decision_ledger/`

**Modelos**:
- `DecisionEvent`: Evento de decisão (imutável, append-only)
- `DecisionLedgerService`: Serviço de persistência + query

**Rotas API**:
```
GET    /enterprise/decisions/history/{startup_id}          → Histórico
GET    /enterprise/decisions/{startup_id}/{template}/{field} → Por campo
GET    /enterprise/decisions/audit/summary/{startup_id}    → Estatísticas
```

**Como usar**:
```python
from backend.enterprise.decision_ledger import DecisionLedgerService

service = DecisionLedgerService(db)
service.record_decision(
    user_id="founder123",
    user_email="founder@startup.com",
    startup_id="startup-abc",
    template_key="persona_01",
    field_key="pain_points",
    new_value="Impossível rastrear pipeline",
    reasoning="Because founders are losing deals",
    source="founder"
)
```

**Feature flag**: `ENTERPRISE_DECISION_LEDGER`

---

### 2️⃣ Method Governance Engine (Validação Declarativa)

**Objetivo**: Enforçar regras do método FCJ sem quebrar fluxo existente.

**O que valida**:
- Campos obrigatórios
- Tamanho mínimo de resposta
- Padrões (regex)
- Coerência entre templates
- Respostas genéricas

**Localização**: `backend/enterprise/governance/`

**Modelos**:
- `ValidationRule`: Uma regra (required, pattern, range, coherence)
- `GovernanceViolation`: Uma violação detectada
- `GovernanceEngine`: Motor de validação

**Rotas API**:
```
POST   /enterprise/governance/validate           → Validar antes de salvar
GET    /enterprise/governance/rules/summary      → Estatísticas
```

**Como usar**:
```python
from backend.enterprise.governance import GovernanceEngine

engine = GovernanceEngine()
violations = engine.validate_template_data(
    template_key="persona_01",
    data={"pain_points": "increase sales", "goals": "more revenue"}
)

for v in violations:
    print(f"{v.field}: {v.message} (severity: {v.risk_level})")
```

**Feature flag**: `ENTERPRISE_METHOD_GOVERNANCE`

---

### 3️⃣ AI Risk Detection & Red Flag System

**Objetivo**: Classificar nível de risco nas respostas sem interferir no output.

**O que detecta**:
- Respostas genéricas (score de genericidade)
- Incoerências com templates relacionados
- Mudanças frequentes (indecisão)
- Falta de alignment ICP → Persona
- Estratégia inconsistente

**Classificações**: low, medium, high, critical

**Localização**: `backend/enterprise/risk_engine/`

**Modelos**:
- `RedFlag`: Bandeira vermelha detectada
- `RiskAssessment`: Avaliação completa
- `RiskDetectionEngine`: Motor de detecção

**Rotas API**:
```
POST   /enterprise/risk/assess-field         → Avaliar um campo
POST   /enterprise/risk/assess-template      → Avaliar template completo
GET    /enterprise/risk/red-flags/{startup}  → Red flags recentes
```

**Como usar**:
```python
from backend.enterprise.risk_engine import RiskDetectionEngine

engine = RiskDetectionEngine()
assessment = engine.assess_field_response(
    template_key="persona_01",
    field_key="pain_points",
    value="aumentar vendas"  # Genérico!
)

print(f"Risk: {assessment.overall_risk}")  # high
print(f"Trust score: {assessment.trust_score}")  # 0.35
```

**Feature flag**: `ENTERPRISE_RISK_ENGINE`

---

### 4️⃣ Cognitive Memory Layer (Persistência Estratégica)

**Objetivo**: Conectar decisões entre etapas e validar coerência ao longo do tempo.

**O que armazena**:
- Valor decidido
- Contexto rico (dados relacionados naquele momento)
- Reasoning (por quê foi decidido)
- Implications (consequências esperadas)
- Inference automática (síntese)

**Localização**: `backend/enterprise/cognitive_memory/`

**Modelos**:
- `StrategicMemory`: Memória persistida (append-only)
- `CognitiveMemoryService`: Serviço de query

**Rotas API**:
```
GET    /enterprise/memory/context/{startup_id}        → Contexto estratégico
GET    /enterprise/memory/related/{startup}/{template}/{field} → Relacionados
```

**Como usar**:
```python
from backend.enterprise.cognitive_memory import CognitiveMemoryService

service = CognitiveMemoryService(db)
service.record_memory(
    startup_id="startup-abc",
    template_key="icp_01",
    field_key="company_size",
    value="small",
    implications=[
        "Focus on cost-sensitive buyers",
        "Need viral growth channel"
    ]
)

# Depois, recuperar contexto
context = service.get_strategic_context("startup-abc")
```

**Feature flag**: `ENTERPRISE_COGNITIVE_MEMORY`

---

### 5️⃣ Dynamic Template Engine (Orquestração)

**Objetivo**: Branch logic, versionamento de metodologia, customização por vertical.

**O que faz**:
- Rotas de templates (ICP-first, Persona-first, etc)
- Branch logic (se respondeu X, próximo é Y)
- Versionamento de método (v1.0, v1.5, v2.0)
- Fallback para sistema existente

**Localização**: `backend/enterprise/template_engine/`

**Modelos**:
- `TemplateNode`: Um template na rota
- `TemplateRoute`: Uma sequência de templates
- `DynamicTemplateEngine`: Motor de orquestração

**Rotas API**:
```
GET    /enterprise/templates/routes                  → Rotas disponíveis
GET    /enterprise/templates/routes/{route}/progress → Progress
GET    /enterprise/templates/routes/{route}/next     → Próximo template
```

**Como usar**:
```python
from backend.enterprise.template_engine import DynamicTemplateEngine

engine = DynamicTemplateEngine()
route = engine.get_route("icp_first")
next_template = engine.get_next_template(
    route_id="icp_first",
    current_template_id="icp_01",
    completed_fields={"company_size": "small"}
)

print(next_template.template_id)  # persona_01
```

**Feature flag**: `ENTERPRISE_TEMPLATE_ENGINE`

---

### 6️⃣ AI Audit & Compliance Layer

**Objetivo**: Registrar TUDO que a IA fez para compliance e auditabilidade.

**O que registra**:
- Qual prompt foi usado (hash + versão)
- Qual modelo respondeu (gpt-4, gpt-3.5, etc)
- Tokens consumidos (entrada + saída)
- Latência de resposta
- Regras aplicadas
- Status (sucesso/erro)

**Localização**: `backend/enterprise/ai_audit/`

**Modelos**:
- `AIAuditLog`: Log imutável de evento
- `AIAuditService`: Serviço de logging + query

**Rotas API**:
```
GET    /enterprise/ai-audit/trail/{startup_id}      → Trail completo
GET    /enterprise/ai-audit/stats/{startup_id}      → Performance stats
```

**Como usar**:
```python
from backend.enterprise.ai_audit import AIAuditService

service = AIAuditService(db)
service.log_event(
    user_id="founder123",
    startup_id="startup-abc",
    event_type="mentor_response",
    model="gpt-4",
    tokens_used={"prompt_tokens": 150, "completion_tokens": 200},
    latency_ms=1200,
    success=1
)

# Depois, auditar
stats = service.get_ai_performance_stats("startup-abc")
print(f"Success rate: {stats['success_rate']}%")
```

**Feature flag**: `ENTERPRISE_AI_AUDIT`

---

### 7️⃣ Cognitive Signals Generator (UX Guiada)

**Objetivo**: Gerar sinais estruturados para Frontend melhorar UX cognitiva.

**O que gera**:
- `risk_level`: low, medium, high, critical
- `alert_message`: "Resposta genérica"
- `next_step_hint`: "Próximo: Descrever ICP"
- `reasoning_summary`: "Por quê isso importa..."
- `confidence_score`: 0.0-1.0
- `coherence_issues`: ["Contradiz resposta anterior"]

**Localização**: `backend/enterprise/cognitive_signals/`

**Modelos**:
- `CognitiveSignal`: Um sinal individual
- `CognitiveSignalSet`: Conjunto de sinais
- `CognitiveSignalGenerator`: Gerador

**Rotas API**:
```
POST   /enterprise/signals/field          → Sinais para um campo
POST   /enterprise/signals/template       → Sinais para template
```

**Como usar**:
```python
from backend.enterprise.cognitive_signals import CognitiveSignalGenerator

gen = CognitiveSignalGenerator()
signals = gen.generate_signals_for_response(
    template_key="persona_01",
    field_key="pain_points",
    value="aumentar vendas",  # Genérico
    risk_assessment={"overall_risk": "high", "trust_score": 0.35}
)

# Mergear no payload existente
payload = {...original_payload...}
payload_with_signals = gen.merge_signals_into_payload(payload, signals)
# Frontend agora recebe: {..., "cognitive_signals": {...}}
```

**Feature flag**: `ENTERPRISE_COGNITIVE_SIGNALS`

---

### 8️⃣ Verticalization & Method Versioning

**Objetivo**: Suporte a múltiplas verticais (SaaS, Marketplace, Indústria, Agro, etc).

**O que suporta**:
- Versões do método (v1.0, v1.5, v2.0)
- Templates específicos por vertical
- Regras de governança por vertical
- Caminhos de migração de versão

**Localização**: `backend/enterprise/method_registry/`

**Modelos**:
- `MethodVersion`: Uma versão do método FCJ
- `MethodRegistry`: Registry central

**Rotas API**:
```
GET    /enterprise/method/versions              → Versões disponíveis
GET    /enterprise/method/versions/{version}    → Detalhes de versão
GET    /enterprise/method/verticals             → Verticais suportadas
GET    /enterprise/method/verticals/{v}/templates → Templates por vertical
GET    /enterprise/method/migration-path        → Sugerir upgrade
```

**Como usar**:
```python
from backend.enterprise.method_registry import MethodRegistry, VerticalType

registry = MethodRegistry()

# Checar se versão suporta vertical
compatible = registry.is_version_compatible_with_vertical("v1.0", VerticalType.MARKETPLACE)
# False - v1.0 só suporta SaaS

# Sugerir upgrade
migration = registry.suggest_migration_path("v1.0", VerticalType.MARKETPLACE)
print(migration["recommended_version"])  # v1.5
```

**Feature flag**: `ENTERPRISE_VERTICALIZATION`

---

## 🔌 INTEGRAÇÃO COM MAIN.PY

Para ativar os subsistemas, adicione estas rotas ao FastAPI app:

```python
# backend/main.py

from fastapi import FastAPI
from backend.enterprise.config import get_or_create_enterprise_config
from backend.enterprise.decision_ledger import router as decision_router
from backend.enterprise.governance import router as governance_router
from backend.enterprise.risk_engine import router as risk_router
from backend.enterprise.cognitive_memory import router as memory_router
from backend.enterprise.template_engine import router as template_router
from backend.enterprise.ai_audit import router as audit_router
from backend.enterprise.cognitive_signals import router as signals_router
from backend.enterprise.method_registry import router as method_router

app = FastAPI()

# Carrega config
config = get_or_create_enterprise_config()

# Registra rotas enterprise (opcionais, controladas por flags)
if config.is_any_enabled():
    logger.info("🏛️  Registrando Enterprise subsistemas...")
    
    if config.decision_ledger:
        app.include_router(decision_router)
    if config.method_governance:
        app.include_router(governance_router)
    if config.risk_engine:
        app.include_router(risk_router)
    if config.cognitive_memory:
        app.include_router(memory_router)
    if config.template_engine:
        app.include_router(template_router)
    if config.ai_audit:
        app.include_router(audit_router)
    if config.cognitive_signals:
        app.include_router(signals_router)
    if config.verticalization:
        app.include_router(method_router)
```

---

## 🚀 ATIVAÇÃO GRADUAL (RECOMENDADO)

**Fase 1 (Week 1)**: Validação e auditoria
```
ENTERPRISE_DECISION_LEDGER=true
ENTERPRISE_AI_AUDIT=true
```
(Observar, não interferir)

**Fase 2 (Week 2)**: Governance e Risk
```
+ ENTERPRISE_METHOD_GOVERNANCE=true
+ ENTERPRISE_RISK_ENGINE=true
```
(Validar, avisar, não bloquear)

**Fase 3 (Week 3)**: Inteligência
```
+ ENTERPRISE_COGNITIVE_MEMORY=true
+ ENTERPRISE_COGNITIVE_SIGNALS=true
```
(Conectar contexto, melhorar UX)

**Fase 4 (Week 4)**: Orquestração
```
+ ENTERPRISE_TEMPLATE_ENGINE=true
+ ENTERPRISE_VERTICALIZATION=true
```
(Rotas dinâmicas, suporte a verticais)

---

## 📊 MIGRATIONS DE DATABASE

Cada subsistema adiciona tabelas novas. Criar migrations:

```bash
# Decision Ledger
alembic revision --autogenerate -m "Add DecisionEvent table"

# Governance (sem nova tabela, apenas validação)

# Risk Engine (sem nova tabela, apenas inference)

# Cognitive Memory
alembic revision --autogenerate -m "Add StrategicMemory table"

# Template Engine (sem nova tabela, usa TemplateRoute em memory)

# AI Audit
alembic revision --autogenerate -m "Add AIAuditLog table"

# Cognitive Signals (sem nova tabela, apenas gerador)

# Method Registry (sem nova tabela, usa registry em memory)

# Executar
alembic upgrade head
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

Antes de ativar em produção:

- [ ] Todas as tabelas criadas com migrations
- [ ] Feature flags testadas (ativadas uma por uma)
- [ ] Sem quebras no sistema existente
- [ ] Performance OK (verificar latências)
- [ ] Logs funcionando
- [ ] APIs respondendo corretamente
- [ ] Frontend consegue consumir cognitive_signals
- [ ] Admin dashboard mostra decision history
- [ ] Relatórios de auditoria funcionam

---

## 🎯 RESULTADO ESPERADO

Um sistema que:
- ✅ Rastreia cada decisão (Decision Ledger)
- ✅ Valida método (Governance)
- ✅ Detecta risco (Risk Engine)
- ✅ Memoriza contexto (Cognitive Memory)
- ✅ Orquestra templates dinamicamente (Template Engine)
- ✅ Audita IA (AI Audit)
- ✅ Guia UX (Cognitive Signals)
- ✅ Suporta múltiplas verticais (Method Registry)
- ✅ SEM quebrar o sistema atual
- ✅ 100% compatível com produção existente
- ✅ Pronto para virar produto FCJ oficial
"""
