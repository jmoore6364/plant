"""
Security module.

Provides authentication, authorization, input validation, and audit logging.
"""

from src.security.auth import (
    JWTAuthenticator,
    TokenData,
    User,
    UserManager,
    get_current_user,
    require_role,
    hash_password,
    verify_password,
    get_user_manager,
)

from src.security.oauth import (
    OAuthClient,
    OAuthManager,
    OAuthToken,
    OAuthUserInfo,
    get_oauth_manager,
)

from src.security.api_keys import (
    APIKey,
    APIKeyManager,
    get_api_key_manager,
    verify_api_key,
    require_scope,
)

from src.security.validation import (
    InputValidator,
    sanitize,
    validate_email,
    validate_username,
    validate_url,
)

from src.security.middleware import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    IPWhitelistMiddleware,
    setup_cors,
    setup_security_middleware,
)

from src.security.secrets_scanner import (
    SecretsScanner,
    LogFilter,
    setup_secrets_filtering,
    redact_dict,
    safe_log,
)

from src.security.audit import (
    AuditEventType,
    AuditEvent,
    AuditLogger,
    get_audit_logger,
    audit_log,
    audit_login_success,
    audit_login_failure,
    audit_access_denied,
)

__all__ = [
    # Authentication
    "JWTAuthenticator",
    "TokenData",
    "User",
    "UserManager",
    "get_current_user",
    "require_role",
    "hash_password",
    "verify_password",
    "get_user_manager",
    # OAuth
    "OAuthClient",
    "OAuthManager",
    "OAuthToken",
    "OAuthUserInfo",
    "get_oauth_manager",
    # API Keys
    "APIKey",
    "APIKeyManager",
    "get_api_key_manager",
    "verify_api_key",
    "require_scope",
    # Validation
    "InputValidator",
    "sanitize",
    "validate_email",
    "validate_username",
    "validate_url",
    # Middleware
    "SecurityHeadersMiddleware",
    "RequestLoggingMiddleware",
    "IPWhitelistMiddleware",
    "setup_cors",
    "setup_security_middleware",
    # Secrets scanning
    "SecretsScanner",
    "LogFilter",
    "setup_secrets_filtering",
    "redact_dict",
    "safe_log",
    # Audit logging
    "AuditEventType",
    "AuditEvent",
    "AuditLogger",
    "get_audit_logger",
    "audit_log",
    "audit_login_success",
    "audit_login_failure",
    "audit_access_denied",
]
