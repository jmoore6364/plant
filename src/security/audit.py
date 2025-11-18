"""
Audit logging system.

Tracks security-relevant events and user actions.
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_CREATED = "token_created"
    TOKEN_REFRESHED = "token_refreshed"
    TOKEN_REVOKED = "token_revoked"

    # Authorization events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"

    # API key events
    API_KEY_CREATED = "api_key_created"
    API_KEY_USED = "api_key_used"
    API_KEY_REVOKED = "api_key_revoked"
    API_KEY_EXPIRED = "api_key_expired"

    # Data events
    DATA_READ = "data_read"
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"

    # Configuration events
    CONFIG_CHANGED = "config_changed"
    SETTINGS_UPDATED = "settings_updated"

    # Security events
    SECURITY_ALERT = "security_alert"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    VULNERABILITY_DETECTED = "vulnerability_detected"

    # System events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    ERROR_OCCURRED = "error_occurred"


class AuditEvent(BaseModel):
    """Audit event model."""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    result: str  # success, failure, error
    details: Dict[str, Any] = {}
    severity: str = "info"  # info, warning, error, critical


class AuditLogger:
    """Log and store audit events."""

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = Path(log_file) if log_file else Path("logs/audit.log")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Set up file logger
        self.file_logger = logging.getLogger("audit")
        self.file_logger.setLevel(logging.INFO)

        # File handler
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter('%(message)s'))

        self.file_logger.addHandler(fh)

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        result: str = "success",
        details: Dict[str, Any] = None,
        severity: str = "info"
    ) -> AuditEvent:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            user_id: User ID
            username: Username
            ip_address: IP address
            resource: Resource being accessed
            action: Action performed
            result: Result (success/failure/error)
            details: Additional details
            severity: Event severity

        Returns:
            AuditEvent
        """
        event = AuditEvent(
            event_id=f"audit_{int(datetime.utcnow().timestamp() * 1000)}",
            timestamp=datetime.utcnow(),
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            resource=resource,
            action=action,
            result=result,
            details=details or {},
            severity=severity
        )

        # Log to file as JSON
        self.file_logger.info(event.json())

        # Also log to console for important events
        if severity in ["error", "critical"]:
            logger.error(f"Audit: {event_type.value} - {username or user_id} - {result}")
        elif severity == "warning":
            logger.warning(f"Audit: {event_type.value} - {username or user_id} - {result}")

        return event

    def log_login_success(self, user_id: str, username: str, ip_address: str):
        """Log successful login."""
        return self.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            action="login",
            result="success",
            severity="info"
        )

    def log_login_failure(self, username: str, ip_address: str, reason: str):
        """Log failed login attempt."""
        return self.log_event(
            event_type=AuditEventType.LOGIN_FAILURE,
            username=username,
            ip_address=ip_address,
            action="login",
            result="failure",
            details={"reason": reason},
            severity="warning"
        )

    def log_access_denied(self, user_id: str, resource: str, reason: str):
        """Log access denial."""
        return self.log_event(
            event_type=AuditEventType.ACCESS_DENIED,
            user_id=user_id,
            resource=resource,
            action="access",
            result="denied",
            details={"reason": reason},
            severity="warning"
        )

    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        result: str = "success"
    ):
        """Log data access."""
        event_type = {
            "read": AuditEventType.DATA_READ,
            "create": AuditEventType.DATA_CREATED,
            "update": AuditEventType.DATA_UPDATED,
            "delete": AuditEventType.DATA_DELETED,
            "export": AuditEventType.DATA_EXPORTED,
        }.get(action.lower(), AuditEventType.DATA_READ)

        return self.log_event(
            event_type=event_type,
            user_id=user_id,
            resource=resource,
            action=action,
            result=result,
            severity="info" if result == "success" else "warning"
        )

    def log_security_alert(
        self,
        alert_type: str,
        details: Dict[str, Any],
        severity: str = "warning"
    ):
        """Log security alert."""
        return self.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            action=alert_type,
            result="alert",
            details=details,
            severity=severity
        )

    def log_api_key_usage(
        self,
        key_id: str,
        resource: str,
        result: str = "success"
    ):
        """Log API key usage."""
        return self.log_event(
            event_type=AuditEventType.API_KEY_USED,
            user_id=key_id,
            resource=resource,
            action="api_request",
            result=result,
            severity="info"
        )

    def query_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> list[AuditEvent]:
        """
        Query audit events.

        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            start_time: Filter by start time
            end_time: Filter by end time
            severity: Filter by severity
            limit: Maximum results

        Returns:
            List of matching audit events
        """
        events = []

        if not self.log_file.exists():
            return events

        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    event_data = json.loads(line)
                    event = AuditEvent(**event_data)

                    # Apply filters
                    if event_type and event.event_type != event_type:
                        continue
                    if user_id and event.user_id != user_id:
                        continue
                    if start_time and event.timestamp < start_time:
                        continue
                    if end_time and event.timestamp > end_time:
                        continue
                    if severity and event.severity != severity:
                        continue

                    events.append(event)

                    if len(events) >= limit:
                        break

                except Exception as e:
                    logger.error(f"Error parsing audit log line: {e}")

        return events


# Global audit logger
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# Convenience functions
def audit_log(event_type: AuditEventType, **kwargs):
    """Log an audit event."""
    logger = get_audit_logger()
    return logger.log_event(event_type, **kwargs)


def audit_login_success(user_id: str, username: str, ip_address: str):
    """Log successful login."""
    logger = get_audit_logger()
    return logger.log_login_success(user_id, username, ip_address)


def audit_login_failure(username: str, ip_address: str, reason: str):
    """Log failed login."""
    logger = get_audit_logger()
    return logger.log_login_failure(username, ip_address, reason)


def audit_access_denied(user_id: str, resource: str, reason: str):
    """Log access denial."""
    logger = get_audit_logger()
    return logger.log_access_denied(user_id, resource, reason)
