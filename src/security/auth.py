"""
JWT authentication system.

Provides token-based authentication for API endpoints.
"""

import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from pydantic import BaseModel

from src.config import get_config

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security
security = HTTPBearer()


class TokenData(BaseModel):
    """JWT token data."""
    user_id: str
    username: str
    email: Optional[str] = None
    roles: list[str] = []
    exp: datetime


class User(BaseModel):
    """User model."""
    id: str
    username: str
    email: str
    hashed_password: str
    roles: list[str] = ["user"]
    is_active: bool = True
    created_at: datetime = datetime.utcnow()


class JWTAuthenticator:
    """Handle JWT token creation and validation."""

    def __init__(self):
        config = get_config()
        self.secret_key = config.security.jwt_secret_key
        self.algorithm = config.security.jwt_algorithm
        self.expiration_minutes = config.security.jwt_expiration_minutes

    def create_access_token(
        self,
        user_id: str,
        username: str,
        email: Optional[str] = None,
        roles: list[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User ID
            username: Username
            email: Email address
            roles: User roles
            expires_delta: Custom expiration time

        Returns:
            JWT token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expiration_minutes)

        to_encode = {
            "sub": user_id,
            "username": username,
            "email": email,
            "roles": roles or ["user"],
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> TokenData:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenData object

        Raises:
            HTTPException if token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token: missing subject")

            return TokenData(
                user_id=user_id,
                username=payload.get("username"),
                email=payload.get("email"),
                roles=payload.get("roles", []),
                exp=datetime.fromtimestamp(payload.get("exp"))
            )

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    def refresh_token(self, token: str) -> str:
        """
        Refresh an existing token.

        Args:
            token: Current JWT token

        Returns:
            New JWT token
        """
        token_data = self.verify_token(token)

        return self.create_access_token(
            user_id=token_data.user_id,
            username=token_data.username,
            email=token_data.email,
            roles=token_data.roles
        )


# Dependency injection
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> TokenData:
    """
    Get current authenticated user from JWT token.

    Usage in FastAPI:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user": user.username}
    """
    token = credentials.credentials
    authenticator = JWTAuthenticator()
    return authenticator.verify_token(token)


async def require_role(required_roles: list[str]):
    """
    Require specific roles for access.

    Usage:
        @app.get("/admin")
        async def admin_route(user: TokenData = Depends(get_current_user)):
            await require_role(["admin"])(user)
            return {"message": "Admin access granted"}
    """
    async def role_checker(user: TokenData = Depends(get_current_user)):
        if not any(role in user.roles for role in required_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )
        return user

    return role_checker


# Password utilities
def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# User management (in-memory store for demo - use database in production)
class UserManager:
    """Manage users and authentication."""

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.users_by_username: Dict[str, User] = {}

    def create_user(
        self,
        username: str,
        password: str,
        email: str,
        roles: list[str] = None
    ) -> User:
        """Create a new user."""
        if username in self.users_by_username:
            raise ValueError(f"Username '{username}' already exists")

        user_id = f"user_{len(self.users) + 1}"
        user = User(
            id=user_id,
            username=username,
            email=email,
            hashed_password=hash_password(password),
            roles=roles or ["user"]
        )

        self.users[user_id] = user
        self.users_by_username[username] = user

        logger.info(f"User created: {username}")
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        user = self.users_by_username.get(username)
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.users_by_username.get(username)

    def update_user_roles(self, user_id: str, roles: list[str]) -> bool:
        """Update user roles."""
        user = self.users.get(user_id)
        if not user:
            return False

        user.roles = roles
        logger.info(f"Updated roles for user {user_id}: {roles}")
        return True

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user."""
        user = self.users.get(user_id)
        if not user:
            return False

        user.is_active = False
        logger.info(f"User deactivated: {user_id}")
        return True


# Global user manager
_user_manager = UserManager()


def get_user_manager() -> UserManager:
    """Get global user manager instance."""
    return _user_manager
