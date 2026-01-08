# 🔐 SECRETS & CREDENTIALS MANAGEMENT

**IMPORTANT:** This file documents how to manage secrets for TR4CTION Agent V2

## Environment Variables That Need Secrets

### 1. JWT_SECRET_KEY (CRITICAL)
**Purpose:** Sign and verify JWT authentication tokens  
**Current Value:** Default dev secret (UNSAFE for production)  
**Generate New:**
```bash
openssl rand -hex 32
```
**Example Output:**
```
a7f3e5c9b2d1f8e4a6c3b9d2e5f8a1c4d7e9f0b2c4d6e8f9a1b3c5d7e9f0b2
```
**Location in .env:**
```
JWT_SECRET_KEY=a7f3e5c9b2d1f8e4a6c3b9d2e5f8a1c4d7e9f0b2c4d6e8f9a1b3c5d7e9f0b2
```
**When to Change:**
- ⚠️ REQUIRED before AWS deployment
- After each security incident
- Every 90 days (security best practice)

---

### 2. Database Password (SQLite - No Password Used)
**Current:** SQLite doesn't require password  
**Future:** When migrating to PostgreSQL:
```bash
openssl rand -base64 32
```
**Would be used in DATABASE_URL:**
```
DATABASE_URL=postgresql://user:PASSWORD@db:5432/tr4ction
```

---

### 3. CORS_ORIGINS
**Purpose:** Allowed domains for frontend communication  
**Development:**
```
http://127.0.0.1:3000
http://localhost:3000
http://127.0.0.1:8000
http://localhost:8000
http://127.0.0.1:3001
http://localhost:3001
```
**Production:**
```
https://tr4ction-v2-agent.vercel.app
https://www.tr4ction-v2-agent.vercel.app
https://api.tr4ction.ai
```

---

### 4. Admin Credentials (Default)
⚠️ **CHANGE IMMEDIATELY ON FIRST LOGIN**

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@tr4ction.com | admin123 |
| Founder | demo@tr4ction.com | demo123 |

**How to Change:**
1. Login to http://localhost:8000/docs (dev)
2. Use `/auth/register` or admin panel
3. Update password via `/auth/change-password`

---

## Security Best Practices

### ✅ DO's
- ✅ Generate new JWT_SECRET_KEY for production
- ✅ Store secrets in environment variables (not code)
- ✅ Use AWS Secrets Manager / Parameter Store
- ✅ Rotate secrets every 90 days
- ✅ Log access to sensitive operations
- ✅ Use HTTPS only in production
- ✅ Enable rate limiting on auth endpoints
- ✅ Require strong passwords

### ❌ DON'Ts
- ❌ Never commit .env files to git
- ❌ Never share secrets in Slack/Email
- ❌ Never use same secret across environments
- ❌ Never log sensitive data
- ❌ Never expose secrets in error messages
- ❌ Never use default passwords in production
- ❌ Never hardcode secrets in code

---

## Managing Secrets in AWS

### 1. AWS Secrets Manager (Recommended)
```bash
# Store JWT secret
aws secretsmanager create-secret \
  --name tr4ction/jwt-secret \
  --secret-string $(openssl rand -hex 32)

# Retrieve in application
# backend/config.py should load from Secrets Manager
```

### 2. AWS Systems Manager Parameter Store
```bash
# Store JWT secret
aws ssm put-parameter \
  --name /tr4ction/jwt-secret \
  --value $(openssl rand -hex 32) \
  --type SecureString

# Retrieve in application
aws ssm get-parameter --name /tr4ction/jwt-secret --with-decryption
```

### 3. Environment Variables (EC2)
```bash
# In /home/ubuntu/tr4ction/.env
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export DATABASE_PASSWORD=$(openssl rand -base64 32)
```

---

## Credential Rotation Procedures

### Weekly Review
```bash
# Check who accessed admin functions
docker compose logs backend | grep -i "admin\|auth"

# Review authentication logs
cat /var/log/tr4ction/auth.log
```

### Monthly Rotation
```bash
# Generate new JWT secret
NEW_SECRET=$(openssl rand -hex 32)

# Update .env
echo "JWT_SECRET_KEY=$NEW_SECRET" >> backend/.env

# Restart backend (existing tokens become invalid)
docker compose restart backend
```

### Quarterly Audit
- [ ] Review all credentials
- [ ] Check for exposed secrets
- [ ] Verify password complexity requirements
- [ ] Test secret rotation procedure
- [ ] Update documentation

---

## Emergency Secret Revocation

### If Secret is Compromised

1. **Immediately revoke JWT tokens:**
   ```python
   # In backend admin console
   from backend.db.database import SessionLocal
   from backend.db.models import TokenBlacklist
   
   session = SessionLocal()
   session.execute("DELETE FROM token_blacklist")
   session.commit()
   ```

2. **Generate new JWT_SECRET_KEY:**
   ```bash
   openssl rand -hex 32
   ```

3. **Update and restart:**
   ```bash
   # Edit backend/.env
   export JWT_SECRET_KEY=<new-value>
   docker compose restart backend
   ```

4. **Force re-authentication:**
   - All existing tokens invalid
   - Users must login again

5. **Audit trail:**
   - Document incident time
   - Note which secret was compromised
   - Update security logs

---

## Password Policy

### Requirements for User Accounts
- **Minimum Length:** 12 characters
- **Complexity:** Uppercase + Lowercase + Numbers + Symbols
- **Expiration:** 90 days
- **History:** Last 5 passwords cannot be reused
- **Lockout:** 5 failed attempts → 30 minute lockout

### For Service Accounts
- **Length:** 32+ characters (random)
- **Type:** Generated with `openssl rand -base64 32`
- **Storage:** AWS Secrets Manager
- **Rotation:** Every 30 days

---

## Audit Logging

### What Gets Logged
```python
# Auth events
- Login attempts (success/failure)
- Token generation
- Password changes
- API key creation/revocation

# Admin events
- User creation/deletion
- Permission changes
- Configuration changes
- Database backups
```

### Viewing Logs
```bash
# Application logs
docker compose logs backend | grep -i "auth\|security"

# System logs
tail -f /var/log/tr4ction/security.log

# AWS CloudWatch (if using)
aws logs get-log-events --log-group-name /aws/tr4ction
```

---

## Credential Recovery Procedures

### Lost Admin Password
1. **Connect to EC2:**
   ```bash
   ssh -i key.pem ubuntu@<IP>
   ```

2. **Reset via database:**
   ```bash
   docker compose exec backend bash
   
   python -c "
   from backend.db.models import User
   from backend.db.database import SessionLocal
   from backend.services.auth import hash_password
   
   session = SessionLocal()
   user = session.query(User).filter(User.email == 'admin@tr4ction.com').first()
   user.password = hash_password('newpassword123')
   session.commit()
   "
   ```

3. **Login with new password:**
   ```bash
   curl -X POST http://api.tr4ction.ai/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@tr4ction.com","password":"newpassword123"}'
   ```

### Lost JWT Secret
1. **Generate new:**
   ```bash
   openssl rand -hex 32
   ```

2. **Update and deploy:**
   ```bash
   # Edit backend/.env
   docker compose restart backend
   ```

3. **Note:** All existing tokens become invalid

---

## Secrets Checklist

### Pre-Production
- [ ] Generated unique JWT_SECRET_KEY
- [ ] Changed admin password
- [ ] Changed founder password
- [ ] Configured CORS_ORIGINS
- [ ] Set ENVIRONMENT=production
- [ ] Set DEBUG_MODE=false
- [ ] Configured database backup
- [ ] Enabled HTTPS

### Post-Deployment
- [ ] Verified secrets not in logs
- [ ] Tested secret rotation
- [ ] Documented secret locations
- [ ] Set up monitoring
- [ ] Trained team on security
- [ ] Scheduled rotation reminders
- [ ] Created incident response plan

---

## Tools for Secret Management

### Local Development
```bash
# Generate random strings
openssl rand -hex 32      # For hex
openssl rand -base64 32   # For base64

# Check if secret exposed
grep -r "JWT_SECRET" .    # Should only be in .env.example
```

### Production (AWS)
```bash
# Secrets Manager
aws secretsmanager create-secret \
  --name tr4ction/jwt-secret \
  --secret-string <value>

# Parameter Store
aws ssm put-parameter \
  --name /tr4ction/jwt-secret \
  --value <value> \
  --type SecureString
```

### Monitoring
```bash
# CloudTrail (tracks API calls)
aws cloudtrail lookup-events --max-results 10

# Config (tracks config changes)
aws configservice get-config-history \
  --resource-type AWS::SecretsManager::Secret
```

---

## Reference: Default Credentials

### Development Only
```
Admin Email:    admin@tr4ction.com
Admin Password: admin123
Founder Email:  demo@tr4ction.com
Founder Pass:   demo123
```

⚠️ **THESE MUST BE CHANGED BEFORE GOING TO PRODUCTION**

---

## Support & Documentation

- **AWS Secrets Manager:** https://docs.aws.amazon.com/secretsmanager/
- **Parameter Store:** https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html
- **Security Best Practices:** https://owasp.org/www-community/
- **Incident Response:** Contact security@tr4ction.ai

---

**Last Updated:** 2026-01-08  
**Version:** 1.0  
**Status:** ✅ Review Regularly
