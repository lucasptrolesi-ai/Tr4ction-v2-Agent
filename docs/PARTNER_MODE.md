# Partner Mode - TR4CTION Agent V2

## Overview

Partner Mode permite que TR4CTION suporte múltiplos parceiros (corporates, universidades, programas de aceleração) sem duplicação de código ou fork do sistema core. Toda customização é feita via **configuração de dados** (DB/YAML), mantendo um único codebase.

## Filosofia de Design

### 1. Configuration-over-Code
- **Zero hardcoded logic**: Nenhum `if partner == "X"`
- **Data-driven**: Tudo customizável via DB/JSON
- **Versionable**: Mudanças auditáveis e rastreáveis
- **Fail-safe**: Sistema funciona perfeitamente sem partner context (fallback FCJ)

### 2. Single Core, Multiple Faces
- **Um método core**: FCJ permanece como base universal
- **Customização superficial**: Tom de linguagem, branding, feature flags
- **Conteúdo imutável**: Logic e templates compartilhados
- **Partner-specific**: Apenas forma de comunicação muda

### 3. Feature Flags First
- **All OFF by default**: Partner mode desabilitado até explicitamente ativado
- **Backward compatible**: Cliente sem partner_id funciona como sempre
- **Gradual rollout**: Partners podem ser adicionados sem afetar existentes

## Architecture

### Partner Model

```python
class Partner(Base):
    __tablename__ = "partners"
    
    id: str              # e.g., "corporate_x", "university_y"
    name: str            # Display name
    description: str     # What this partner represents
    language_tone: str   # "consultative" | "educational" | "executive" | "technical"
    default_method_version: str  # e.g., "1.0", "2.0"
    feature_overrides: JSON      # Partner-specific flags
```

**Campos:**
- `language_tone`: Define como cognitive signals são apresentados (form, não content)
- `feature_overrides`: JSON com flags específicas do parceiro (ex: `{"enable_ai_mentor": true}`)

### Vertical Model

```python
class Vertical(Base):
    __tablename__ = "verticals"
    
    id: str
    partner_id: str      # FK -> partners
    name: str            # "SaaS", "Marketplace", "Agro", etc.
    available_templates: JSON  # Lista de template_keys permitidos
    governance_gates_ref: JSON  # Referências a gates específicos
    risk_rules_ref: JSON        # Referências a regras de risco
```

**Campos:**
- `available_templates`: JSON array `["mvp_canvas", "customer_discovery"]`
- `governance_gates_ref`: JSON array com IDs de gates relevantes ao vertical
- `risk_rules_ref`: JSON array com IDs de regras de risco

### MethodProfile Model

```python
class MethodProfile(Base):
    __tablename__ = "method_profiles"
    
    id: str
    partner_id: str
    vertical_id: str (optional)
    method_version: str
    effective_language_tone: str
    template_customizations: JSON
```

Combina partner + vertical + version para gerar profile de execução.

## Language Tone System

### Variants

Quatro tons disponíveis, aplicados aos **prefixes** de cognitive signals:

| Tone          | Alert Prefix | Learning Prefix | Target Audience |
|---------------|--------------|-----------------|-----------------|
| consultative  | Revisar      | Aprendizado     | Founders padrão |
| educational   | Vamos revisar | Vamos aprender | Universidades   |
| executive     | Atenção      | Insight         | C-level         |
| technical     | Validação    | Análise técnica | Equipes técnicas|

### Example

**Conteúdo (imutável):**
> "Business model incompleto. Adicione canais de distribuição."

**Forma (muda com tone):**
- **Consultative**: "Revisar: Business model incompleto..."
- **Educational**: "Vamos revisar: Business model incompleto..."
- **Executive**: "Atenção: Business model incompleto..."
- **Technical**: "Validação: Business model incompleto..."

⚠️ **Importante**: Content NÃO muda, apenas prefixes/styling.

## Usage Examples

### 1. Default FCJ (sem partner)

```python
POST /founder/answer
{
  "trail_id": "discovery",
  "step_id": "mvp_canvas",
  "formData": {...}
}
```

**Behavior:**
- Partner ID: `fcj_default`
- Language tone: `consultative`
- All templates available
- Standard FCJ flow

### 2. Corporate Partner

```python
POST /founder/answer
{
  "trail_id": "discovery",
  "step_id": "mvp_canvas",
  "formData": {...},
  "partner_id": "corporate_x",
  "vertical_id": "saas"
}
```

**Behavior:**
- Partner ID: `corporate_x`
- Language tone: `executive` (from partner config)
- Templates filtered by `saas` vertical
- Governance gates filtered by vertical
- Cognitive signals use "Atenção:" prefix

### 3. University Program

```python
POST /founder/answer
{
  ...
  "partner_id": "university_y",
  "vertical_id": null
}
```

**Behavior:**
- Partner ID: `university_y`
- Language tone: `educational`
- All templates available (no vertical filtering)
- "Vamos revisar:" prefix in signals

## Configuration Workflow

### Step 1: Create Partner

```python
from backend.enterprise.multi_vertical.models import Partner, PartnerService

partner = Partner(
    id="corporate_acme",
    name="Acme Corp Innovation Lab",
    description="Internal startup studio",
    language_tone="executive",
    default_method_version="1.0",
    feature_overrides={"enable_ai_mentor": True}
)
db.add(partner)
db.commit()
```

### Step 2: Create Verticals (Optional)

```python
from backend.enterprise.multi_vertical.models import Vertical

vertical_saas = Vertical(
    id="acme_saas",
    partner_id="corporate_acme",
    name="SaaS B2B",
    available_templates=[
        "mvp_canvas",
        "customer_discovery",
        "unit_economics"
    ],
    governance_gates_ref=["gate_mvp_validation"],
    risk_rules_ref=["rule_market_risk"]
)
db.add(vertical_saas)
db.commit()
```

### Step 3: Build Context in Runtime

```python
from backend.enterprise.multi_vertical.context import ContextBuilder

builder = ContextBuilder(db)
context = builder.build(
    startup_id="startup_123",
    user_id="user_456",
    template_key="mvp_canvas",
    partner_id="corporate_acme",
    vertical_id="acme_saas"
)

# context.language_tone = "executive"
# context.available_templates = ["mvp_canvas", "customer_discovery", "unit_economics"]
```

## Feature Flag

### Enable Partner Mode

```bash
# .env
ENTERPRISE_MULTI_VERTICAL=true
```

```python
# config.py
config.multi_vertical = True
```

### Disable (Default)

```bash
# No flag set
```

**Behavior:**
- `compute_cognitive_signals` ignores partner_id/vertical_id
- `ContextBuilder` returns FCJ defaults
- Zero impact on existing clients

## Migration

### Apply Schema

```bash
cd backend/scripts/migrations
python 20260108_phase4_multi_vertical.py --up
```

**Creates:**
- `partners` table
- `verticals` table
- `method_profiles` table
- Seeds `fcj_default` partner

### Rollback

```bash
python 20260108_phase4_multi_vertical.py --down
```

## Testing

### Unit Tests

```python
def test_partner_language_tone():
    partner = PartnerService.get_or_default("corporate_x")
    assert partner.language_tone == "executive"

def test_vertical_template_filtering():
    vertical = VerticalService.get_or_default("acme_saas")
    templates = vertical.available_templates
    assert "mvp_canvas" in templates
    assert "fundraising" not in templates
```

### Integration Tests

```python
def test_cognitive_signals_with_partner_context():
    response = client.post("/founder/answer", json={
        "trail_id": "discovery",
        "step_id": "mvp_canvas",
        "formData": {...},
        "partner_id": "corporate_x",
        "vertical_id": "saas"
    })
    signals = response.json()["cognitive_signals"]
    assert signals["partner_id"] == "corporate_x"
    assert "Atenção:" in signals["alerts"][0]["message"]
```

## Security Considerations

### 1. Partner Isolation
- Partners não veem dados de outros partners
- Vertical filtering previne acesso não autorizado a templates
- Audit logs incluem partner_id

### 2. Feature Overrides Validation
- `feature_overrides` validado via Pydantic schema
- Não permite override de flags críticas (ex: `audit_enabled`)

### 3. Fail-Safe Defaults
- Erro em partner context → fallback para FCJ
- Missing partner_id → `fcj_default`
- Invalid vertical_id → all templates available

## Roadmap

### Phase 4.1 (Current)
- ✅ Partner/Vertical/MethodProfile models
- ✅ Language tone system
- ✅ Context builder
- ✅ Governance/risk integration

### Phase 4.2 (Next)
- Template customization per vertical
- Partner-specific branding (logo, colors)
- Custom trails per partner
- Multi-language support

### Phase 4.3 (Future)
- Partner analytics dashboard
- White-label mode
- Revenue sharing models
- Partner API keys

## Support

Questions? Contact:
- **Engineering**: `tech@tr4ction.com`
- **Documentation**: See `MULTI_VERTICAL_STRATEGY.md`
- **Version Management**: See `METHOD_VERSIONING.md`
