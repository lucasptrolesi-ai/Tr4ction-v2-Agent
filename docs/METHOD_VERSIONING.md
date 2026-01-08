# Method Versioning - TR4CTION Agent V2

## Overview

Method Versioning permite que TR4CTION evolua o método FCJ (Founder Challenge Journey) ao longo do tempo sem quebrar startups existentes. Cada versão do método pode ter:
- Templates diferentes
- Governance gates atualizados
- Risk rules refinados
- Language/UX improvements

**Key Principle:** Startups em uma versão do método continuam nela até explicitamente migrarem.

## Version Format

Semantic versioning: `MAJOR.MINOR`

- **MAJOR**: Breaking changes (ex: remover templates core, reestruturar trails)
- **MINOR**: Additive changes (ex: novos templates, gates refinados, UX improvements)

Examples:
- `1.0`: FCJ original (Phases 1-3)
- `1.1`: Phase 4 (multi-vertical, partner mode)
- `2.0`: Future major evolution (ex: different trail structure)

## Version Model

### MethodProfile

```python
class MethodProfile(Base):
    __tablename__ = "method_profiles"
    
    id: str
    partner_id: str              # FK -> partners
    vertical_id: str (optional)  # FK -> verticals
    method_version: str          # e.g., "1.0", "1.1"
    effective_language_tone: str
    template_customizations: JSON
```

**Purpose:**
- Combines partner + vertical + version
- Defines what method configuration a startup uses
- Immutable once assigned (for stability)

### Partner.default_method_version

```python
class Partner(Base):
    default_method_version: str = "1.0"  # New partners get this version
```

**Purpose:**
- Partners can specify default version for new startups
- Allows partners to stay on stable versions while TR4CTION evolves

## Version Compatibility Matrix

| Version | Templates        | Governance     | Risk Engine   | Backward Compatible |
|---------|------------------|----------------|---------------|---------------------|
| 1.0     | FCJ Core         | Phase 2 gates  | Phase 2 rules | N/A                 |
| 1.1     | FCJ + Vertical   | Phase 4 gates  | Phase 4 rules | ✅ Yes (additive)   |
| 2.0     | FCJ Evolution    | Refined gates  | ML-based risk | ⚠️ Migration needed |

## Version Lifecycle

### 1. Active Versions
Currently supported and maintained:
- Bug fixes
- Security patches
- Minor improvements (within MINOR version)

**Current Active:** `1.0`, `1.1`

### 2. Deprecated Versions
Still functional but no longer receiving updates:
- Existing startups continue working
- New startups cannot use deprecated versions
- Encouraged to migrate

**Current Deprecated:** None

### 3. Sunset Versions
No longer supported, migration required:
- Hard cutoff date announced 6 months in advance
- Automated migration tools provided
- Support team assists with migration

**Current Sunset:** None

## Version Assignment

### New Startups

```python
# Automatic assignment via partner
POST /founder/startup/create
{
  "name": "My Startup",
  "partner_id": "corporate_x"  # Has default_method_version = "1.1"
}

# Response includes:
{
  "startup_id": "startup_123",
  "method_version": "1.1",  # From partner.default_method_version
  ...
}
```

### Existing Startups (Legacy)

```python
# Automatically assigned version 1.0 on first use
# Stored in startup metadata or inferred from creation_date
```

**Inference Logic:**
```python
def infer_method_version(startup: Startup) -> str:
    # Startups created before Phase 4 → 1.0
    if startup.created_at < datetime(2026, 1, 8):
        return "1.0"
    
    # Startups created after Phase 4 → 1.1 (or partner default)
    partner = PartnerService.get_or_default(startup.partner_id)
    return partner.default_method_version
```

## Version Features

### Version 1.0 (FCJ Core)

**Includes:**
- Core FCJ templates:
  - MVP Canvas
  - Customer Discovery
  - Unit Economics
  - Go-to-Market
  - Fundraising Strategy
- Phase 2 Governance Gates (method_governance)
- Phase 2 Risk Detection (risk_engine)
- Phase 3 Cognitive UX (cognitive_signals)
- Observability Framework (audit, ledger)

**Missing:**
- Multi-vertical support
- Partner mode
- Language tone variants
- Vertical-specific governance/risk

### Version 1.1 (Phase 4)

**Adds:**
- Multi-vertical configuration
- Partner mode with language tones
- Vertical-aware template filtering
- Vertical-aware governance gates
- Vertical-aware risk rules
- MethodProfile model

**Backward Compatible:**
- All 1.0 features still work
- Startups without partner_id → FCJ default (same as 1.0)
- New features are opt-in via flags

### Version 2.0 (Future)

**Proposed Features:**
- ML-based risk detection
- Automated template suggestions
- Dynamic trail generation
- Real-time collaboration
- Advanced analytics dashboard

**Breaking Changes:**
- Trail structure might change
- Some templates might be retired
- Governance gates might be consolidated
- Migration tools provided

## Version Migration

### Migration Workflow

#### Step 1: Announce Migration

```
Subject: TR4CTION Method Upgrade Available: 1.0 → 1.1

Hello [Founder],

TR4CTION just released version 1.1 with these improvements:
- Multi-vertical support (customize experience for your type of business)
- Enhanced cognitive signals with personalized language
- Vertical-specific guidance (less noise, more relevant)

What this means for you:
- Your current work is safe (no data loss)
- You can opt-in to upgrade (it's free)
- After migration, you'll see improved recommendations

How to migrate:
1. Click "Upgrade to 1.1" in Settings
2. Review changes (we'll show a preview)
3. Confirm migration
4. Continue your journey with better tools

Questions? Reply to this email or contact support.
```

#### Step 2: Preview Changes

```python
POST /founder/startup/{startup_id}/preview_migration
{
  "target_version": "1.1",
  "vertical_id": "saas_b2b"  # Optional: test with vertical
}

# Response:
{
  "current_version": "1.0",
  "target_version": "1.1",
  "changes": {
    "new_templates": ["template_x"],
    "removed_templates": [],  # None in 1.1 (additive)
    "governance_changes": "3 new gates added",
    "risk_changes": "2 new rules added",
    "data_migration": "None required"
  },
  "estimated_impact": "Low - additive changes only",
  "rollback_available": true
}
```

#### Step 3: Execute Migration

```python
POST /founder/startup/{startup_id}/migrate
{
  "target_version": "1.1",
  "vertical_id": "saas_b2b"
}

# Backend actions:
1. Backup current state (in case of rollback)
2. Update startup.method_version = "1.1"
3. Create MethodProfile with partner + vertical
4. Re-evaluate governance/risk with new rules
5. Update cognitive_signals with new language_tone
6. Log migration in audit trail
7. Return success response
```

#### Step 4: Rollback (if needed)

```python
POST /founder/startup/{startup_id}/rollback_migration
{
  "target_version": "1.0"
}

# Restores previous state from backup
```

### Automated Migration (for 1.0 → 1.1)

Since 1.1 is **additive only**, automated migration is safe:

```python
# backend/scripts/migrations/migrate_1_0_to_1_1.py

def migrate_startup_to_1_1(startup_id: str, db: Session):
    startup = db.query(Startup).filter_by(id=startup_id).first()
    
    if startup.method_version != "1.0":
        raise ValueError("Startup not on version 1.0")
    
    # Update version
    startup.method_version = "1.1"
    
    # Create MethodProfile (if has partner)
    if startup.partner_id:
        partner = PartnerService.get_or_default(startup.partner_id)
        profile = MethodProfile(
            id=f"profile_{startup_id}",
            partner_id=partner.id,
            vertical_id=startup.vertical_id,  # May be None
            method_version="1.1",
            effective_language_tone=partner.language_tone
        )
        db.add(profile)
    
    # Log migration
    AuditService.log(
        entity_type="startup",
        entity_id=startup_id,
        event_type="method_version_migration",
        metadata={
            "from_version": "1.0",
            "to_version": "1.1",
            "automated": True
        }
    )
    
    db.commit()
    print(f"✅ Migrated {startup_id} to 1.1")
```

Run for all startups:
```bash
python backend/scripts/migrations/migrate_1_0_to_1_1.py --all
```

## Version Detection

### Runtime Version Check

```python
# backend/enterprise/multi_vertical/context.py

class ContextBuilder:
    def build(
        self,
        startup_id: str,
        user_id: str,
        template_key: str,
        partner_id: Optional[str] = None,
        vertical_id: Optional[str] = None,
    ) -> ExecutionContext:
        # Detect method version
        startup = self._get_startup(startup_id)
        method_version = startup.method_version or self._infer_version(startup)
        
        # Build context based on version
        if method_version == "1.0":
            return self._build_v1_0_context(...)
        elif method_version == "1.1":
            return self._build_v1_1_context(...)
        else:
            raise ValueError(f"Unsupported method version: {method_version}")
```

### Frontend Version Display

```javascript
// Display current method version in UI
<div className="method-version">
  <span>TR4CTION Method v{startup.method_version}</span>
  {upgrade_available && (
    <button onClick={showUpgradeModal}>
      Upgrade to v{latest_version} ✨
    </button>
  )}
</div>
```

## Version-Specific Features

### Conditional Features

```python
# Example: AI Mentor only in 1.1+
if method_version >= "1.1" and config.multi_vertical:
    ai_mentor_response = ai_mentor_service.generate_guidance(...)
else:
    ai_mentor_response = None  # Not available in 1.0
```

### Feature Flags per Version

```python
# config.py
VERSION_FEATURES = {
    "1.0": {
        "method_governance": True,
        "risk_engine": True,
        "cognitive_signals": True,
        "multi_vertical": False,  # Not in 1.0
    },
    "1.1": {
        "method_governance": True,
        "risk_engine": True,
        "cognitive_signals": True,
        "multi_vertical": True,  # Added in 1.1
    }
}

def get_features_for_version(version: str) -> Dict[str, bool]:
    return VERSION_FEATURES.get(version, VERSION_FEATURES["1.0"])
```

## Testing Across Versions

### Version-Specific Tests

```python
# tests/test_version_compatibility.py

def test_1_0_startup_uses_default_language():
    startup = create_startup(method_version="1.0")
    signals = compute_cognitive_signals(
        template_key="mvp_canvas",
        data={},
        db=db,
        startup_id=startup.id
    )
    # 1.0 should use "consultative" (no language_tone param)
    assert "Revisar:" in signals["alerts"][0]["message"]

def test_1_1_startup_uses_partner_language():
    partner = create_partner(language_tone="executive")
    startup = create_startup(
        method_version="1.1",
        partner_id=partner.id
    )
    signals = compute_cognitive_signals(
        template_key="mvp_canvas",
        data={},
        db=db,
        startup_id=startup.id,
        partner_id=partner.id
    )
    # 1.1 should use partner's language_tone
    assert "Atenção:" in signals["alerts"][0]["message"]
```

### Integration Tests

```python
def test_migration_1_0_to_1_1():
    # Create 1.0 startup
    startup = create_startup(method_version="1.0")
    answer_1_0 = submit_answer(startup.id, template_key="mvp_canvas", data={})
    
    # Migrate to 1.1
    migrate_startup_to_1_1(startup.id)
    
    # Submit same answer in 1.1
    answer_1_1 = submit_answer(startup.id, template_key="mvp_canvas", data={})
    
    # Verify backward compatibility
    assert answer_1_1["template_key"] == answer_1_0["template_key"]
    assert "cognitive_signals" in answer_1_1  # Still present
```

## Version Documentation

Each version has:
- Release notes (`RELEASE_NOTES_1_1.md`)
- Migration guide (`MIGRATION_1_0_TO_1_1.md`)
- Feature comparison table (in this doc)
- Deprecation warnings (if applicable)

### Example Release Notes

**TR4CTION Method v1.1 - Release Notes**

**Release Date:** January 8, 2026

**What's New:**
- Multi-vertical support (SaaS, Marketplace, Agro, Fintech)
- Partner mode with language tone variants
- Vertical-aware governance gates
- Enhanced cognitive signals with context
- MethodProfile model for versioning

**Improvements:**
- Reduced false positives in risk detection
- Faster template selection (filtered by vertical)
- Better language adaptation for different audiences

**Backward Compatibility:**
- All 1.0 features work unchanged
- Startups without partner_id continue as before
- Migration is optional (can stay on 1.0)

**Migration:**
- Automated migration available via Settings → Upgrade
- Zero downtime, rollback available
- No data loss, fully reversible

**Deprecations:**
- None (1.1 is additive)

**Known Issues:**
- None

## Best Practices

### 1. Default to Latest Stable
New partners should use latest stable version:
```python
partner.default_method_version = "1.1"  # Not beta versions
```

### 2. Test Before Rolling Out
Test new versions with subset of users before mass migration:
```python
# Gradual rollout
migrate_users = User.filter(beta_tester=True)
for user in migrate_users:
    migrate_startup_to_1_1(user.startup_id)
```

### 3. Provide Rollback Window
Allow 30 days to rollback after migration:
```python
if (now - migration_date).days <= 30:
    allow_rollback = True
```

### 4. Communicate Changes
Inform users about version changes:
- Release notes in app
- Email notifications
- What's New modal on first login after upgrade

### 5. Version in API Responses
Include method_version in API responses for debugging:
```json
{
  "startup_id": "startup_123",
  "method_version": "1.1",
  "trail_id": "discovery",
  ...
}
```

## Support

Questions? See:
- **Partner Configuration**: `PARTNER_MODE.md`
- **Vertical Strategy**: `MULTI_VERTICAL_STRATEGY.md`
- **Engineering**: `tech@tr4ction.com`
- **Release Notes**: `docs/releases/`
