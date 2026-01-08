# Multi-Vertical Strategy - TR4CTION Agent V2

## Overview

Multi-Vertical Strategy permite que TR4CTION adapte o método FCJ para diferentes tipos de negócios (SaaS, Marketplace, Agro, Industry, etc.) sem criar forks de código. Cada vertical tem:
- Templates relevantes filtrados
- Governance gates específicos
- Regras de risco customizadas
- Linguagem adaptada ao contexto

## Core Principles

### 1. One Method, Multiple Contexts
- **FCJ é universal**: Serve como base para todos os verticals
- **Filtering, not forking**: Verticais filtram templates existentes, não criam novos
- **Context-aware execution**: Governance/risk consideram contexto do vertical
- **Backward compatible**: Startups sem vertical usam FCJ completo

### 2. Data-Driven Configuration
- **No code changes**: Vertical definido via DB/JSON
- **Template references**: JSON arrays apontam para templates existentes (zero duplication)
- **Rule references**: Governance/risk rules reusados entre verticals
- **Versionable**: Mudanças de vertical auditáveis

### 3. Progressive Enhancement
- **Start broad, refine later**: Iniciar com todos templates, filtrar gradualmente
- **User feedback driven**: Ajustar vertical baseado em dados reais
- **A/B testable**: Comparar eficácia de diferentes configurações

## Vertical Model

### Schema

```python
class Vertical(Base):
    __tablename__ = "verticals"
    
    id: str                     # e.g., "saas_b2b", "marketplace_local"
    partner_id: str             # FK -> partners
    name: str                   # Display name
    description: str            # What this vertical represents
    available_templates: JSON   # Array of template_keys
    governance_gates_ref: JSON  # Array of gate IDs
    risk_rules_ref: JSON        # Array of rule IDs
```

### Field Details

#### available_templates
JSON array de `template_key` strings:

```json
{
  "available_templates": [
    "mvp_canvas",
    "customer_discovery",
    "unit_economics",
    "pricing_strategy"
  ]
}
```

**Purpose:**
- Lista whitelist de templates aplicáveis ao vertical
- Templates não listados são **hidden** (não aparecerão em trails)
- `null` ou `[]` = todos templates disponíveis

#### governance_gates_ref
JSON array de IDs de governance gates:

```json
{
  "governance_gates_ref": [
    "gate_mvp_validation",
    "gate_customer_evidence",
    "gate_market_sizing"
  ]
}
```

**Purpose:**
- Filtra quais gates são aplicáveis a este vertical
- Gates não referenciados são ignorados
- Permite governance focada no que importa para o tipo de negócio

#### risk_rules_ref
JSON array de IDs de regras de risco:

```json
{
  "risk_rules_ref": [
    "rule_market_risk",
    "rule_competition_analysis",
    "rule_revenue_model"
  ]
}
```

**Purpose:**
- Filtra regras de risco relevantes
- Reduce false positives (ex: não checar B2C metrics em SaaS B2B)
- Personaliza cognitive signals por tipo de startup

## Vertical Examples

### 1. SaaS B2B

**Characteristics:**
- Sales cycles longos
- Customer acquisition focado em enterprise
- Pricing baseado em valor/seat
- Churn crítico

**Configuration:**

```python
vertical_saas = Vertical(
    id="saas_b2b",
    partner_id="fcj_default",
    name="SaaS B2B",
    description="Software as a Service for business clients",
    available_templates=[
        "mvp_canvas",
        "customer_discovery",
        "unit_economics",
        "pricing_strategy",
        "churn_analysis",
        "sales_playbook"
    ],
    governance_gates_ref=[
        "gate_mvp_validation",
        "gate_customer_interviews",
        "gate_pricing_validation"
    ],
    risk_rules_ref=[
        "rule_churn_risk",
        "rule_cac_payback",
        "rule_enterprise_pipeline"
    ]
)
```

**Why these templates?**
- `unit_economics`: LTV/CAC crítico em SaaS
- `churn_analysis`: Retention é survival metric
- `sales_playbook`: Enterprise sales é complexo

**Why these gates?**
- `gate_pricing_validation`: Pricing errors são fatais em SaaS
- `gate_customer_interviews`: Product-market fit validation

### 2. Marketplace Local

**Characteristics:**
- Two-sided network
- Local logistics/operations
- GMV-based economics
- Supply/demand balance critical

**Configuration:**

```python
vertical_marketplace = Vertical(
    id="marketplace_local",
    partner_id="fcj_default",
    name="Marketplace Local",
    description="Two-sided platforms connecting local supply and demand",
    available_templates=[
        "mvp_canvas",
        "marketplace_dynamics",
        "unit_economics",
        "operations_plan",
        "supplier_acquisition",
        "demand_generation"
    ],
    governance_gates_ref=[
        "gate_supply_demand_balance",
        "gate_unit_economics_marketplace",
        "gate_operations_validation"
    ],
    risk_rules_ref=[
        "rule_liquidity_risk",
        "rule_supply_concentration",
        "rule_logistics_feasibility"
    ]
)
```

**Why these templates?**
- `marketplace_dynamics`: Understand chicken-and-egg problem
- `supplier_acquisition`: Supply side critical
- `operations_plan`: Logistics complexity

**Why these gates?**
- `gate_supply_demand_balance`: Must validate both sides
- `gate_logistics_feasibility`: Can you actually deliver?

### 3. Agro Tech

**Characteristics:**
- Long sales cycles
- Regulatory complexity
- Seasonality
- Capital intensive

**Configuration:**

```python
vertical_agro = Vertical(
    id="agro_tech",
    partner_id="fcj_default",
    name="Agro Tech",
    description="Technology solutions for agriculture and farming",
    available_templates=[
        "mvp_canvas",
        "customer_discovery",
        "regulatory_compliance",
        "go_to_market_rural",
        "pilot_program",
        "funding_strategy"
    ],
    governance_gates_ref=[
        "gate_regulatory_approval",
        "gate_pilot_results",
        "gate_seasonality_plan"
    ],
    risk_rules_ref=[
        "rule_regulatory_risk",
        "rule_adoption_barriers",
        "rule_capital_requirements"
    ]
)
```

**Why these templates?**
- `regulatory_compliance`: Heavily regulated sector
- `pilot_program`: Proof of concept critical
- `go_to_market_rural`: Different distribution channels

**Why these gates?**
- `gate_regulatory_approval`: Mandatory compliance
- `gate_pilot_results`: Must validate in real conditions

### 4. Fintech

**Characteristics:**
- High regulatory burden
- Trust critical
- Security/compliance
- Capital intensive

**Configuration:**

```python
vertical_fintech = Vertical(
    id="fintech",
    partner_id="fcj_default",
    name="Fintech",
    description="Financial technology and banking solutions",
    available_templates=[
        "mvp_canvas",
        "customer_discovery",
        "regulatory_compliance",
        "security_architecture",
        "trust_building",
        "funding_strategy",
        "compliance_roadmap"
    ],
    governance_gates_ref=[
        "gate_regulatory_approval",
        "gate_security_audit",
        "gate_fraud_prevention",
        "gate_capital_adequacy"
    ],
    risk_rules_ref=[
        "rule_regulatory_risk",
        "rule_security_breach",
        "rule_trust_deficit",
        "rule_capital_burn"
    ]
)
```

**Why these templates?**
- `security_architecture`: Non-negotiable
- `compliance_roadmap`: Regulatory complexity
- `trust_building`: User trust is everything

**Why these gates?**
- `gate_security_audit`: Must pass before launch
- `gate_fraud_prevention`: Protect users and business

## Template Selection Logic

### TemplateSelector (backend/enterprise/multi_vertical/context.py)

```python
class TemplateSelector:
    def filter_by_vertical(
        self,
        all_templates: List[str],
        vertical_id: Optional[str]
    ) -> List[str]:
        if not vertical_id:
            return all_templates  # No filtering
        
        vertical = VerticalService.get_or_default(vertical_id)
        whitelist = vertical.available_templates or []
        
        if not whitelist:
            return all_templates  # Empty = all allowed
        
        return [t for t in all_templates if t in whitelist]
```

**Behavior:**
- No vertical_id → all templates
- Empty whitelist → all templates
- Populated whitelist → filter to listed templates only

### Frontend Integration

Frontend **não precisa saber** sobre verticals:

```javascript
// Frontend request (unchanged)
POST /founder/answer
{
  "trail_id": "discovery",
  "step_id": "mvp_canvas",
  "formData": {...}
}

// Backend transparently applies vertical context
// if partner/vertical is set in user session
```

**Session-based vertical:**
```python
# On login/partner selection
session["partner_id"] = "corporate_x"
session["vertical_id"] = "saas_b2b"

# All subsequent requests use this context automatically
```

## Governance Integration

### Vertical-Aware Gate Evaluation

```python
# backend/enterprise/governance/engine.py

def evaluate_gate_with_vertical(
    gate: GovernanceGate,
    template_key: str,
    data: Dict,
    vertical_id: Optional[str]
) -> GateResult:
    # Check if gate is relevant to vertical
    if vertical_id:
        vertical = VerticalService.get_or_default(vertical_id)
        gate_refs = vertical.governance_gates_ref or []
        
        if gate_refs and gate.id not in gate_refs:
            # Skip gate - not applicable to this vertical
            return GateResult(status="skipped", reason="Not applicable to vertical")
    
    # Evaluate normally
    return evaluate_gate(gate, template_key, data)
```

**Benefits:**
- Reduces noise (fewer irrelevant gates firing)
- Focuses founder on what matters for their type of business
- Maintains audit trail (skipped gates are logged)

## Risk Detection Integration

### Vertical-Aware Risk Assessment

```python
# backend/enterprise/risk/engine.py

def assess_with_vertical(
    template_key: str,
    data: Dict,
    vertical_id: Optional[str]
) -> RiskAssessment:
    # Get vertical-specific risk rules
    active_rules = self.all_risk_rules
    
    if vertical_id:
        vertical = VerticalService.get_or_default(vertical_id)
        rule_refs = vertical.risk_rules_ref or []
        
        if rule_refs:
            active_rules = [r for r in active_rules if r.id in rule_refs]
    
    # Assess with filtered rules
    return self.assess(template_key, data, active_rules)
```

**Benefits:**
- Reduces false positives (ex: não checar metrics B2C em SaaS B2B)
- Personaliza cognitive signals
- Mantém risk engine genérico (rules são reusáveis)

## Configuration Workflow

### Step 1: Define Vertical in Database

```python
from backend.enterprise.multi_vertical.models import Vertical

vertical = Vertical(
    id="saas_b2b",
    partner_id="corporate_x",
    name="SaaS B2B",
    description="B2B SaaS startups",
    available_templates=[
        "mvp_canvas",
        "customer_discovery",
        "unit_economics"
    ],
    governance_gates_ref=["gate_mvp_validation"],
    risk_rules_ref=["rule_churn_risk"]
)
db.add(vertical)
db.commit()
```

### Step 2: Assign to User/Startup

```python
# Option 1: Via partner assignment
POST /admin/users/{user_id}/assign_partner
{
  "partner_id": "corporate_x",
  "vertical_id": "saas_b2b"
}

# Option 2: Via startup metadata
POST /founder/startup/create
{
  "name": "My SaaS Startup",
  "vertical_id": "saas_b2b"
}
```

### Step 3: Validate Template Filtering

```python
from backend.enterprise.multi_vertical.context import TemplateSelector

selector = TemplateSelector()
all_templates = ["mvp_canvas", "customer_discovery", "fundraising"]
filtered = selector.filter_by_vertical(all_templates, "saas_b2b")

# filtered = ["mvp_canvas", "customer_discovery"]
# "fundraising" removed
```

## Testing Strategy

### Unit Tests

```python
def test_vertical_template_filtering():
    vertical = Vertical(
        id="test_vertical",
        partner_id="test_partner",
        available_templates=["template_a", "template_b"]
    )
    
    selector = TemplateSelector()
    all_templates = ["template_a", "template_b", "template_c"]
    filtered = selector.filter_by_vertical(all_templates, vertical.id)
    
    assert "template_a" in filtered
    assert "template_b" in filtered
    assert "template_c" not in filtered
```

### Integration Tests

```python
def test_vertical_governance_filtering():
    # Create vertical with specific gates
    vertical = Vertical(
        id="test_vertical",
        governance_gates_ref=["gate_mvp"]
    )
    
    # Create gates
    gate_mvp = GovernanceGate(id="gate_mvp", ...)
    gate_funding = GovernanceGate(id="gate_funding", ...)
    
    # Evaluate with vertical context
    result = evaluate_gate_with_vertical(
        gate_mvp,
        template_key="mvp_canvas",
        data={},
        vertical_id="test_vertical"
    )
    assert result.status != "skipped"
    
    result = evaluate_gate_with_vertical(
        gate_funding,
        template_key="fundraising",
        data={},
        vertical_id="test_vertical"
    )
    assert result.status == "skipped"
```

## Analytics & Optimization

### Vertical Performance Metrics

Track per vertical:
- Template completion rates
- Time to complete trail
- Governance gate pass/fail rates
- Risk signal frequency
- User satisfaction scores

**Usage:**
```sql
SELECT 
  vertical_id,
  template_key,
  AVG(completion_time) as avg_time,
  COUNT(*) as completions
FROM step_answers
WHERE vertical_id IS NOT NULL
GROUP BY vertical_id, template_key
ORDER BY vertical_id, avg_time DESC;
```

### Vertical Optimization Loop

1. **Collect data**: Track template usage per vertical
2. **Analyze patterns**: Which templates are skipped? Which take too long?
3. **Refine configuration**: Update `available_templates` to remove noise
4. **Validate impact**: Compare completion rates before/after
5. **Iterate**: Continuous improvement

## Migration Path

### For Existing Startups

**Option 1: Automatic Classification**
```python
# Classify based on existing data
def auto_classify_vertical(startup_data: Dict) -> str:
    keywords = startup_data.get("description", "").lower()
    
    if "saas" in keywords or "software" in keywords:
        return "saas_b2b"
    elif "marketplace" in keywords:
        return "marketplace_local"
    elif "agro" in keywords or "farm" in keywords:
        return "agro_tech"
    
    return None  # No vertical (use full FCJ)
```

**Option 2: Gradual Migration**
```python
# Start with no filtering, gradually add verticals
# Existing startups: vertical_id = NULL (full access)
# New startups: assigned vertical on creation
```

## Feature Flag

Enable multi-vertical:

```bash
# .env
ENTERPRISE_MULTI_VERTICAL=true
```

Disable (default):
```bash
# No flag = all templates available to everyone
```

## Best Practices

### 1. Start Broad
- Don't over-filter initially
- Let users explore, then refine based on data

### 2. Document Rationale
- Explain why templates are included/excluded
- Keep configuration transparent

### 3. Test with Real Users
- Validate template filtering doesn't block critical paths
- Ensure governance gates are achievable

### 4. Version Control
- Track changes to vertical configurations
- A/B test different configurations

### 5. Fail-Safe Defaults
- If vertical_id is missing/invalid → full FCJ
- Don't break existing flows

## Support

Questions? See:
- **Partner Configuration**: `PARTNER_MODE.md`
- **Method Versioning**: `METHOD_VERSIONING.md`
- **Engineering**: `tech@tr4ction.com`
