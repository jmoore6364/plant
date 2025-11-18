"""
API key management system.

Provides API key generation, validation, and rotation.
"""

import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pydantic import BaseModel
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKey(BaseModel):
    """API key model."""
    key_id: str
    key_hash: str  # Hashed version of the key
    name: str
    description: Optional[str] = None
    scopes: List[str] = []  # Permissions/scopes
    rate_limit: int = 1000  # Requests per hour
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0


class APIKeyManager:
    """Manage API keys."""

    def __init__(self):
        self.keys: Dict[str, APIKey] = {}  # key_id -> APIKey
        self.key_hashes: Dict[str, str] = {}  # key_hash -> key_id

    def generate_key(
        self,
        name: str,
        description: Optional[str] = None,
        scopes: List[str] = None,
        rate_limit: int = 1000,
        expires_in_days: Optional[int] = None
    ) -> tuple[str, APIKey]:
        """
        Generate a new API key.

        Args:
            name: Key name
            description: Key description
            scopes: Permissions/scopes
            rate_limit: Requests per hour
            expires_in_days: Expiration in days

        Returns:
            (raw_key, APIKey) - Store raw_key securely, it won't be shown again
        """
        # Generate random key
        raw_key = f"sha_{secrets.token_urlsafe(32)}"

        # Hash the key for storage
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # Create key ID
        key_id = f"key_{len(self.keys) + 1}"

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create API key
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            description=description,
            scopes=scopes or ["read"],
            rate_limit=rate_limit,
            expires_at=expires_at
        )

        # Store key
        self.keys[key_id] = api_key
        self.key_hashes[key_hash] = key_id

        logger.info(f"API key generated: {name} (ID: {key_id})")

        return raw_key, api_key

    def validate_key(self, raw_key: str) -> Optional[APIKey]:
        """
        Validate an API key.

        Args:
            raw_key: Raw API key string

        Returns:
            APIKey if valid, None otherwise
        """
        # Hash the provided key
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # Find key by hash
        key_id = self.key_hashes.get(key_hash)
        if not key_id:
            return None

        api_key = self.keys.get(key_id)
        if not api_key:
            return None

        # Check if active
        if not api_key.is_active:
            logger.warning(f"Inactive API key used: {key_id}")
            return None

        # Check if expired
        if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
            logger.warning(f"Expired API key used: {key_id}")
            return None

        # Update usage statistics
        api_key.last_used_at = datetime.utcnow()
        api_key.usage_count += 1

        return api_key

    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        api_key = self.keys.get(key_id)
        if not api_key:
            return False

        api_key.is_active = False
        logger.info(f"API key revoked: {key_id}")
        return True

    def delete_key(self, key_id: str) -> bool:
        """Delete an API key."""
        api_key = self.keys.get(key_id)
        if not api_key:
            return False

        # Remove from storage
        self.key_hashes.pop(api_key.key_hash, None)
        self.keys.pop(key_id, None)

        logger.info(f"API key deleted: {key_id}")
        return True

    def list_keys(self, include_inactive: bool = False) -> List[APIKey]:
        """List all API keys."""
        keys = list(self.keys.values())

        if not include_inactive:
            keys = [k for k in keys if k.is_active]

        return keys

    def get_key(self, key_id: str) -> Optional[APIKey]:
        """Get API key by ID."""
        return self.keys.get(key_id)

    def rotate_key(self, key_id: str) -> tuple[str, APIKey]:
        """
        Rotate an API key (generate new key, keep same permissions).

        Args:
            key_id: Existing key ID

        Returns:
            (new_raw_key, new_APIKey)
        """
        old_key = self.keys.get(key_id)
        if not old_key:
            raise ValueError(f"API key not found: {key_id}")

        # Generate new key with same settings
        new_raw_key, new_key = self.generate_key(
            name=old_key.name,
            description=f"Rotated from {key_id}",
            scopes=old_key.scopes,
            rate_limit=old_key.rate_limit
        )

        # Revoke old key
        old_key.is_active = False

        logger.info(f"API key rotated: {key_id} -> {new_key.key_id}")

        return new_raw_key, new_key

    def check_scope(self, api_key: APIKey, required_scope: str) -> bool:
        """Check if API key has required scope."""
        return required_scope in api_key.scopes or "admin" in api_key.scopes

    def get_usage_stats(self, key_id: str) -> Dict:
        """Get usage statistics for an API key."""
        api_key = self.keys.get(key_id)
        if not api_key:
            return {}

        return {
            "key_id": key_id,
            "name": api_key.name,
            "usage_count": api_key.usage_count,
            "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            "created_at": api_key.created_at.isoformat(),
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "is_active": api_key.is_active,
            "rate_limit": api_key.rate_limit,
        }


# Global API key manager
_api_key_manager = APIKeyManager()


def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager instance."""
    return _api_key_manager


# FastAPI dependency
async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> APIKey:
    """
    Verify API key from request header.

    Usage:
        @app.get("/protected")
        async def protected_route(key: APIKey = Depends(verify_api_key)):
            return {"message": "Access granted"}
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    manager = get_api_key_manager()
    validated_key = manager.validate_key(api_key)

    if not validated_key:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")

    return validated_key


async def require_scope(required_scopes: List[str]):
    """
    Require specific scopes for API key.

    Usage:
        @app.get("/admin")
        async def admin_route(key: APIKey = Depends(verify_api_key)):
            await require_scope(["admin"])(key)
            return {"message": "Admin access granted"}
    """
    async def scope_checker(key: APIKey = Depends(verify_api_key)):
        manager = get_api_key_manager()

        if not any(manager.check_scope(key, scope) for scope in required_scopes):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required scopes: {required_scopes}"
            )

        return key

    return scope_checker
