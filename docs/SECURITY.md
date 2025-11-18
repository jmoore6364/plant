# Security Guide

Comprehensive security documentation for the System Health Analyzer.

## Table of Contents

- [Authentication](#authentication)
- [Authorization](#authorization)
- [API Security](#api-security)
- [Secrets Management](#secrets-management)
- [Input Validation](#input-validation)
- [Audit Logging](#audit-logging)
- [Security Headers](#security-headers)
- [Best Practices](#best-practices)

---

## Authentication

### JWT Authentication

Token-based authentication for API access.

#### Generate Token

```python
from src.security import JWTAuthenticator

auth = JWTAuthenticator()
token = auth.create_access_token(
    user_id="user123",
    username="admin",
    email="admin@example.com",
    roles=["admin", "user"]
)

print(f"Token: {token}")
```

#### Use Token

```bash
curl http://localhost:8000/api/protected \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

#### Refresh Token

```python
new_token = auth.refresh_token(old_token)
```

#### Protect Endpoints

```python
from fastapi import Depends
from src.security import get_current_user, TokenData

@app.get("/protected")
async def protected_route(user: TokenData = Depends(get_current_user)):
    return {"user": user.username, "roles": user.roles}
```

### OAuth 2.0

Integration with external identity providers.

#### Supported Providers

- Google
- GitHub
- Microsoft

#### Setup OAuth

```python
from src.security import OAuthManager

# Register provider
manager = OAuthManager()
manager.register_provider(
    "google",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Get authorization URL
auth_url = manager.get_authorization_url(
    "google",
    redirect_uri="https://app.example.com/callback",
    state="random-state-token"
)

# Exchange code for token
result = await manager.authenticate(
    "google",
    code="authorization-code",
    redirect_uri="https://app.example.com/callback"
)

print(f"JWT Token: {result['access_token']}")
print(f"User: {result['user']}")
```

#### OAuth Endpoints

```python
from fastapi import Request
from src.security import get_oauth_manager

@app.get("/auth/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    manager = get_oauth_manager()
    auth_url = manager.get_authorization_url(
        provider,
        redirect_uri=str(request.url_for("oauth_callback", provider=provider))
    )
    return {"authorization_url": auth_url}

@app.get("/auth/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str):
    manager = get_oauth_manager()
    result = await manager.authenticate(provider, code, redirect_uri="...")
    return result
```

---

## Authorization

### Role-Based Access Control (RBAC)

#### Define Roles

Built-in roles:
- `user`: Basic access
- `admin`: Full access
- `operator`: Limited admin access
- `readonly`: Read-only access

#### Require Roles

```python
from src.security import require_role, get_current_user

@app.post("/admin/users")
async def create_user(user: TokenData = Depends(get_current_user)):
    # Check role
    await require_role(["admin"])(user)
    # Only admins can access this
    return {"message": "User created"}
```

#### Check Permissions

```python
from src.security import get_current_user

@app.delete("/api/data/{id}")
async def delete_data(id: int, user: TokenData = Depends(get_current_user)):
    if "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    # Delete data
    return {"message": "Deleted"}
```

### API Key Authentication

API keys for programmatic access.

#### Generate API Key

```python
from src.security import APIKeyManager

manager = APIKeyManager()

# Generate key
raw_key, api_key = manager.generate_key(
    name="Production API",
    description="Main production API key",
    scopes=["read", "write", "delete"],
    rate_limit=1000,  # Requests per hour
    expires_in_days=365
)

print(f"API Key: {raw_key}")  # Save this securely!
print(f"Key ID: {api_key.key_id}")
```

#### Use API Key

```bash
curl http://localhost:8000/api/data \
  -H "X-API-Key: sha_your-api-key-here"
```

#### Protect with API Key

```python
from fastapi import Depends
from src.security import verify_api_key, APIKey

@app.get("/api/data")
async def get_data(key: APIKey = Depends(verify_api_key)):
    # Key is valid
    return {"data": "...", "key_name": key.name}
```

#### Require Scopes

```python
from src.security import require_scope

@app.post("/api/data")
async def create_data(key: APIKey = Depends(verify_api_key)):
    # Check scope
    await require_scope(["write"])(key)
    # Only keys with 'write' scope can access
    return {"message": "Created"}
```

#### Rotate API Key

```python
# Rotate to new key
new_raw_key, new_key = manager.rotate_key("key_123")

# Old key is automatically revoked
```

#### Revoke API Key

```python
manager.revoke_key("key_123")
```

---

## API Security

### Rate Limiting

Protect against abuse and DDoS attacks.

#### Configure Rate Limiting

```yaml
# config.yaml
security:
  rate_limit_enabled: true
  rate_limit_requests: 100  # Per period
  rate_limit_period_seconds: 60  # 1 minute
```

#### Rate Limit Middleware

```python
from src.performance import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    requests=100,
    window_seconds=60
)
```

#### Per-Endpoint Rate Limiting

```python
from src.performance import rate_limit

@app.get("/api/expensive")
@rate_limit(requests=10, window_seconds=60)
async def expensive_operation():
    return {"data": "..."}
```

#### Rate Limit Response

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704110460
Retry-After: 60

{
  "detail": "Rate limit exceeded"
}
```

### CORS Configuration

```yaml
# config.yaml
security:
  cors_enabled: true
  allowed_hosts:
    - "https://app.example.com"
    - "https://admin.example.com"

api:
  cors_origins:
    - "https://app.example.com"
```

### Security Headers

Automatically applied headers:

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; ...
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

---

## Secrets Management

### HashiCorp Vault

```bash
# Set up Vault
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=your-vault-token

# Store secrets
vault kv put secret/database/url value="postgresql://..."
vault kv put secret/ai/anthropic_api_key value="sk-ant-..."

# Configure application
# config.yaml
database:
  url: "${secret:database/url}"
```

### AWS Secrets Manager

```bash
# Store secret
aws secretsmanager create-secret \
  --name system-health/database/url \
  --secret-string "postgresql://..."

# Configure application
# config.yaml
database:
  url: "${secret:system-health/database/url}"
```

### Environment Variables

```bash
# .env (development only!)
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET_KEY=your-secret-key

# Production: Use secrets manager
```

### File-Based Secrets

```json
// secrets.json (add to .gitignore!)
{
  "database": {
    "url": "postgresql://..."
  },
  "ai": {
    "anthropic_api_key": "sk-ant-..."
  }
}
```

---

## Input Validation

### Sanitization

```python
from src.security import sanitize, validate_email, validate_url

# Sanitize user input
safe_text = sanitize(
    user_input,
    check_sql=True,
    check_xss=True,
    check_command=True,
    max_length=1000
)

# Validate email
email = validate_email("user@example.com")

# Validate URL
url = validate_url("https://example.com")
```

### Built-in Protections

#### SQL Injection

```python
# ✓ Safe (automatically detected and blocked)
text = sanitize("'; DROP TABLE users; --")
# Raises HTTPException(400, "potential SQL injection")
```

#### XSS Prevention

```python
# ✓ Safe (HTML escaped)
text = sanitize("<script>alert('XSS')</script>")
# Returns: "&lt;script&gt;alert('XSS')&lt;/script&gt;"
```

#### Command Injection

```python
# ✓ Safe (blocked)
text = sanitize("file.txt; rm -rf /")
# Raises HTTPException(400, "potential command injection")
```

#### Path Traversal

```python
# ✓ Safe (blocked)
path = sanitize("../../etc/passwd", check_path=True)
# Raises HTTPException(400, "potential path traversal")
```

### Custom Validation

```python
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    username: str
    email: str

    @validator('username')
    def validate_username(cls, v):
        from src.security import validate_username
        return validate_username(v)

    @validator('email')
    def validate_email(cls, v):
        from src.security import validate_email
        return validate_email(v)
```

---

## Audit Logging

Track security-relevant events.

### Log Events

```python
from src.security import (
    audit_log,
    audit_login_success,
    audit_login_failure,
    audit_access_denied,
    AuditEventType
)

# Login success
audit_login_success(
    user_id="user123",
    username="admin",
    ip_address="192.168.1.100"
)

# Login failure
audit_login_failure(
    username="admin",
    ip_address="192.168.1.100",
    reason="Invalid password"
)

# Access denied
audit_access_denied(
    user_id="user456",
    resource="/admin/users",
    reason="Insufficient permissions"
)

# Custom event
audit_log(
    event_type=AuditEventType.DATA_EXPORTED,
    user_id="user123",
    resource="metrics",
    action="export",
    result="success",
    details={"format": "json", "records": 1000}
)
```

### Query Audit Logs

```python
from src.security import get_audit_logger, AuditEventType
from datetime import datetime, timedelta

logger = get_audit_logger()

# Get failed login attempts
failed_logins = logger.query_events(
    event_type=AuditEventType.LOGIN_FAILURE,
    start_time=datetime.utcnow() - timedelta(hours=24),
    limit=100
)

# Get user activity
user_activity = logger.query_events(
    user_id="user123",
    start_time=datetime.utcnow() - timedelta(days=7),
    limit=1000
)

# Get security alerts
security_alerts = logger.query_events(
    event_type=AuditEventType.SECURITY_ALERT,
    severity="critical",
    limit=50
)
```

### Audit Log Format

```json
{
  "event_id": "audit_1704110400123",
  "timestamp": "2024-01-01T12:00:00Z",
  "event_type": "login_failure",
  "user_id": null,
  "username": "admin",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "resource": null,
  "action": "login",
  "result": "failure",
  "details": {
    "reason": "Invalid password"
  },
  "severity": "warning"
}
```

---

## Security Headers

### Configure Headers

Headers are automatically applied by middleware:

```python
from src.security import setup_security_middleware

# Setup (called in main.py)
setup_security_middleware(app)
```

### Custom Headers

```python
from starlette.middleware.base import BaseHTTPMiddleware

class CustomSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Custom-Header"] = "value"
        return response

app.add_middleware(CustomSecurityMiddleware)
```

---

## Best Practices

### 1. Always Use HTTPS

```yaml
# Enforce HTTPS
security:
  cors_enabled: true

# Nginx configuration
server {
    listen 443 ssl http2;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### 2. Strong Secrets

```python
# ✗ Bad
jwt_secret_key: "secret123"

# ✓ Good (generated securely)
import secrets
jwt_secret_key = secrets.token_urlsafe(32)
```

### 3. Principle of Least Privilege

```python
# Give minimum required permissions
api_key = manager.generate_key(
    name="Analytics API",
    scopes=["read"],  # Only read access
    rate_limit=100
)
```

### 4. Regular Key Rotation

```python
# Rotate keys every 90 days
if key.created_at < datetime.utcnow() - timedelta(days=90):
    new_key = manager.rotate_key(key.key_id)
```

### 5. Monitor Security Events

```python
# Alert on suspicious activity
failed_logins = logger.query_events(
    event_type=AuditEventType.LOGIN_FAILURE,
    ip_address="192.168.1.100",
    start_time=datetime.utcnow() - timedelta(hours=1)
)

if len(failed_logins) > 5:
    # Send alert
    send_security_alert("Multiple failed login attempts")
```

### 6. Input Validation Everywhere

```python
# Always validate user input
@app.post("/api/data")
async def create_data(data: dict):
    # Sanitize all string inputs
    safe_data = {
        k: sanitize(v) if isinstance(v, str) else v
        for k, v in data.items()
    }
    # Process safe_data
```

### 7. Secrets in Logs

```python
# ✗ Bad
logger.info(f"API Key: {api_key}")

# ✓ Good (automatically redacted)
from src.security import safe_log
logger.info(safe_log(f"API Key: {api_key}"))
# Logs: "API Key: [REDACTED]"
```

### 8. Secure Dependencies

```bash
# Check for vulnerabilities
safety check

# Scan code
bandit -r src/

# Update dependencies regularly
pip list --outdated
```

### 9. Rate Limit Everything

```python
# Apply rate limiting to all endpoints
app.add_middleware(RateLimitMiddleware)

# Extra limits for expensive operations
@app.post("/api/analysis")
@rate_limit(requests=10, window_seconds=60)
async def analyze():
    pass
```

### 10. Regular Security Audits

- Review audit logs weekly
- Update dependencies monthly
- Rotate secrets quarterly
- Penetration testing annually

---

## Security Checklist

### Before Production

- [ ] Change all default passwords
- [ ] Generate strong JWT secret (32+ bytes)
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Enable API key authentication
- [ ] Configure CORS properly
- [ ] Enable audit logging
- [ ] Set up secrets management
- [ ] Configure security headers
- [ ] Enable input validation
- [ ] Set up monitoring and alerting
- [ ] Document security procedures
- [ ] Train team on security practices

### Regular Maintenance

- [ ] Review audit logs (weekly)
- [ ] Check for failed login attempts (daily)
- [ ] Update dependencies (monthly)
- [ ] Rotate API keys (quarterly)
- [ ] Review user permissions (quarterly)
- [ ] Security vulnerability scan (monthly)
- [ ] Penetration testing (annually)
- [ ] Incident response drill (quarterly)

---

## Incident Response

### Suspected Breach

1. **Isolate**: Disconnect affected systems
2. **Assess**: Review audit logs
3. **Contain**: Revoke compromised credentials
4. **Investigate**: Determine scope
5. **Remediate**: Fix vulnerabilities
6. **Monitor**: Watch for further attempts
7. **Document**: Record findings
8. **Review**: Update procedures

### Example: Compromised API Key

```python
# Immediately revoke key
manager.revoke_key(compromised_key_id)

# Review usage
audit_logs = logger.query_events(
    user_id=compromised_key_id,
    start_time=datetime.utcnow() - timedelta(days=30)
)

# Generate new key for legitimate user
new_key, _ = manager.generate_key(
    name="Replacement Key",
    scopes=original_scopes
)

# Notify security team
send_alert(f"API key {compromised_key_id} revoked")
```

---

## See Also

- [Configuration Guide](CONFIGURATION.md) - Security configuration options
- [API Reference](API.md) - Authentication endpoints
- [Deployment Guide](DEPLOYMENT.md) - Production security setup
- [Audit Logging](AUDIT.md) - Detailed audit logging guide
