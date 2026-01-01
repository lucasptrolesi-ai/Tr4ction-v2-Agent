# 🔒 CRITICAL Security Issues - Phase 2

## ⚠️ ADDITIONAL CRITICAL VULNERABILITIES FOUND

### 🔴 CRITICAL #1: Missing Authentication on Admin Endpoints

**Status:** ❌ **BLOCKER FOR PRODUCTION**

#### Vulnerable Endpoints (30+)
```
/admin/knowledge (GET, DELETE) - Anyone can list/delete documents
/admin/reset-vector-db (POST) - Anyone can reset entire database
/admin/trails (GET, POST) - Anyone can create/modify trails
/admin/founders/{user_id}/progress - Anyone can access user data
/admin/knowledge/upload - Anyone can upload documents
/admin/knowledge/reindex-all - DoS attack vector
```

#### Impact
- **Data breach:** Unauthorized access to sensitive data
- **Data loss:** Anyone can delete documents/reset DB
- **DoS:** Anyone can trigger expensive operations (reindex-all)
- **Compliance:** Violates LGPD, GDPR, SOC2

#### Recommended Fix
```python
# ANTES (VULNERÁVEL)
@router.get("/admin/knowledge")
async def list_knowledge():
    ...

# DEPOIS (SEGURO)
@router.get("/admin/knowledge")
async def list_knowledge(
    current_admin: User = Depends(get_current_admin)  # ✅ Requires admin auth
):
    ...
```

**Estimated Effort:** 2-4 hours (30+ endpoints to fix)
**Priority:** 🔴 P0 - BLOCKER

---

### 🟡 HIGH #2: CSRF Protection Missing

**Status:** ⚠️ High Risk

#### Problem
All state-changing operations (POST, PUT, DELETE) lack CSRF protection.

#### Attack Scenario
```html
<!-- Malicious site -->
<form action="https://your-api.com/admin/reset-vector-db" method="POST">
  <input type="submit" value="Click for free prize!">
</form>
```

If admin is logged in and clicks → entire DB reset.

#### Recommended Fix
Implement CSRF middleware with token validation:
```python
from fastapi_csrf_protect import CsrfProtect

@app.post("/admin/knowledge/upload")
async def upload(
    csrf_token: str = Header(...),
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf(csrf_token)
    ...
```

**Estimated Effort:** 4-6 hours
**Priority:** 🟡 P1 - High

---

### 🟡 HIGH #3: Rate Limiting Not Applied to Critical Endpoints

**Status:** ⚠️ High Risk (DoS Vector)

#### Problem
Expensive operations have no specific rate limits:
- `/admin/knowledge/reindex-all` - Reprocesses entire KB
- `/admin/knowledge/upload` - No per-user upload limit
- `/chat/` - No per-user query limit

#### Impact
- **DoS:** Attacker can exhaust CPU/memory
- **Cost:** API costs (Groq/OpenAI) can be exploited
- **Performance:** Legitimate users affected

#### Recommended Fix
```python
# Per-endpoint rate limiter
@router.post("/admin/knowledge/reindex-all")
@limiter.limit("1/hour")  # Max 1 per hour
async def reindex_all():
    ...

@router.post("/admin/knowledge/upload")
@limiter.limit("10/minute")  # Max 10 uploads per minute
async def upload():
    ...
```

**Estimated Effort:** 2-3 hours
**Priority:** 🟡 P1 - High

---

### 🔵 MEDIUM #4: SQLAlchemy Query Injection Risk

**Status:** ⚠️ Medium Risk

#### Problem
While using ORM (safer than raw SQL), some queries could be vulnerable if inputs aren't validated:

```python
# Potentially vulnerable if email comes from user without validation
user = db.query(User).filter(User.email == email).first()
```

#### Recommended Fix
Already partially mitigated by Pydantic validators, but add explicit sanitization:
```python
from sqlalchemy import text

# NEVER do this:
# db.execute(f"SELECT * FROM users WHERE email = '{email}'")  # ❌ SQLi

# Instead:
db.query(User).filter(User.email == email).first()  # ✅ Safe (parameterized)
```

**Status:** ✅ Mostly mitigated (ORM + Pydantic)
**Action:** Code review to ensure no raw SQL usage

---

### 🔵 MEDIUM #5: Missing Request ID for Tracing

**Status:** ⚠️ Medium (Operational)

#### Problem
No request tracing in logs makes debugging production issues difficult.

#### Recommended Fix
```python
from uuid import uuid4
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id', default='')

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid4())
    request_id_var.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

**Estimated Effort:** 1-2 hours
**Priority:** 🔵 P2 - Medium

---

## 📊 SECURITY SCORECARD

| Area | Before Phase 1 | After Phase 1 | After Phase 2 (Recommended) |
|------|----------------|---------------|------------------------------|
| **Path Traversal** | ❌ | ✅ | ✅ |
| **Password Security** | ❌ | ✅ | ✅ |
| **Error Handling** | ❌ | ✅ | ✅ |
| **Authentication** | ⚠️ Partial | ⚠️ Partial | ✅ Full |
| **CSRF Protection** | ❌ | ❌ | ✅ |
| **Rate Limiting** | ⚠️ Global | ⚠️ Global | ✅ Per-Endpoint |
| **SQL Injection** | ✅ ORM | ✅ ORM | ✅ Verified |
| **Request Tracing** | ❌ | ❌ | ✅ |

**Overall Security Score:**
- Before: 🔴 D (40/100)
- Phase 1: 🟡 C+ (65/100)
- Phase 2: 🟢 A- (85/100)

---

## 🎯 RECOMMENDED ACTION PLAN

### Immediate (This Week)
1. ✅ **Fix missing authentication on admin endpoints** (BLOCKER)
   - Add `Depends(get_current_admin)` to all 30+ admin endpoints
   - Verify authorization checks

### Short Term (Next Sprint)
2. ⚠️ **Implement CSRF protection**
   - Install `fastapi-csrf-protect`
   - Add CSRF middleware
   - Update frontend to include CSRF tokens

3. ⚠️ **Add per-endpoint rate limiting**
   - Strict limits on expensive operations
   - Per-user upload quotas

### Medium Term (Next Month)
4. 🔵 **Add request tracing**
   - X-Request-ID header
   - Correlation in logs

5. 🔵 **Security audit Phase 3**
   - Penetration testing
   - OWASP ZAP scan
   - Dependency vulnerability scan

---

## ✅ APPROVAL STATUS

**Current State:** ⚠️ **NOT READY FOR PUBLIC PRODUCTION**

**Reason:** Missing authentication on 30+ admin endpoints = critical security breach

**Recommended:** Implement Phase 2 fixes BEFORE public launch

**Timeline:** 1-2 days for authentication fixes (critical path)
