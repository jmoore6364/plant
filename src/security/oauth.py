"""
OAuth 2.0 authentication support.

Supports OAuth providers like Google, GitHub, Microsoft, etc.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from src.security.auth import JWTAuthenticator, UserManager

logger = logging.getLogger(__name__)


class OAuthProvider(BaseModel):
    """OAuth provider configuration."""
    name: str
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    user_info_url: str
    scopes: list[str] = []


class OAuthToken(BaseModel):
    """OAuth token response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class OAuthUserInfo(BaseModel):
    """OAuth user information."""
    provider: str
    provider_user_id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    raw_data: Dict[str, Any] = {}


class OAuthClient:
    """OAuth 2.0 client for third-party authentication."""

    # Predefined providers
    PROVIDERS = {
        "google": OAuthProvider(
            name="google",
            client_id="",
            client_secret="",
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            user_info_url="https://www.googleapis.com/oauth2/v2/userinfo",
            scopes=["openid", "email", "profile"]
        ),
        "github": OAuthProvider(
            name="github",
            client_id="",
            client_secret="",
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            user_info_url="https://api.github.com/user",
            scopes=["user:email"]
        ),
        "microsoft": OAuthProvider(
            name="microsoft",
            client_id="",
            client_secret="",
            authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            user_info_url="https://graph.microsoft.com/v1.0/me",
            scopes=["openid", "email", "profile"]
        ),
    }

    def __init__(self, provider_name: str, client_id: str, client_secret: str):
        """
        Initialize OAuth client.

        Args:
            provider_name: OAuth provider (google, github, microsoft)
            client_id: OAuth client ID
            client_secret: OAuth client secret
        """
        if provider_name not in self.PROVIDERS:
            raise ValueError(f"Unsupported OAuth provider: {provider_name}")

        self.provider = self.PROVIDERS[provider_name].copy()
        self.provider.client_id = client_id
        self.provider.client_secret = client_secret

    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """
        Get authorization URL for OAuth flow.

        Args:
            redirect_uri: Callback URL
            state: CSRF state token

        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.provider.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.provider.scopes),
        }

        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.provider.authorize_url}?{query_string}"

    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str
    ) -> OAuthToken:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code
            redirect_uri: Callback URL

        Returns:
            OAuth token
        """
        data = {
            "client_id": self.provider.client_id,
            "client_secret": self.provider.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.provider.token_url,
                    data=data,
                    headers={"Accept": "application/json"}
                )
                response.raise_for_status()

                token_data = response.json()
                return OAuthToken(**token_data)

        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise HTTPException(status_code=400, detail=f"OAuth token exchange failed: {str(e)}")

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get user information from OAuth provider.

        Args:
            access_token: OAuth access token

        Returns:
            User information
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.provider.user_info_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()

                user_data = response.json()

                # Extract common fields based on provider
                if self.provider.name == "google":
                    user_info = OAuthUserInfo(
                        provider="google",
                        provider_user_id=user_data["id"],
                        email=user_data["email"],
                        name=user_data.get("name"),
                        avatar_url=user_data.get("picture"),
                        raw_data=user_data
                    )
                elif self.provider.name == "github":
                    user_info = OAuthUserInfo(
                        provider="github",
                        provider_user_id=str(user_data["id"]),
                        email=user_data.get("email"),
                        name=user_data.get("name") or user_data.get("login"),
                        avatar_url=user_data.get("avatar_url"),
                        raw_data=user_data
                    )
                elif self.provider.name == "microsoft":
                    user_info = OAuthUserInfo(
                        provider="microsoft",
                        provider_user_id=user_data["id"],
                        email=user_data.get("mail") or user_data.get("userPrincipalName"),
                        name=user_data.get("displayName"),
                        avatar_url=None,
                        raw_data=user_data
                    )
                else:
                    raise ValueError(f"Unsupported provider: {self.provider.name}")

                return user_info

        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to get user info: {str(e)}")

    async def authenticate(
        self,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Complete OAuth authentication flow.

        Args:
            code: Authorization code
            redirect_uri: Callback URL

        Returns:
            dict with JWT token and user info
        """
        # Exchange code for token
        oauth_token = await self.exchange_code_for_token(code, redirect_uri)

        # Get user info
        user_info = await self.get_user_info(oauth_token.access_token)

        # Create or update user in system
        user_manager = UserManager()
        username = f"{user_info.provider}_{user_info.provider_user_id}"

        user = user_manager.get_user_by_username(username)
        if not user:
            # Create new user
            user = user_manager.create_user(
                username=username,
                password="oauth_user",  # OAuth users don't use password
                email=user_info.email,
                roles=["user"]
            )
            logger.info(f"New OAuth user created: {username}")

        # Generate JWT token
        jwt_auth = JWTAuthenticator()
        jwt_token = jwt_auth.create_access_token(
            user_id=user.id,
            username=user.username,
            email=user.email,
            roles=user.roles
        )

        return {
            "access_token": jwt_token,
            "token_type": "Bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": user.roles,
            },
            "oauth_provider": user_info.provider,
        }


class OAuthManager:
    """Manage multiple OAuth providers."""

    def __init__(self):
        self.providers: Dict[str, OAuthClient] = {}

    def register_provider(
        self,
        provider_name: str,
        client_id: str,
        client_secret: str
    ):
        """Register an OAuth provider."""
        client = OAuthClient(provider_name, client_id, client_secret)
        self.providers[provider_name] = client
        logger.info(f"OAuth provider registered: {provider_name}")

    def get_provider(self, provider_name: str) -> Optional[OAuthClient]:
        """Get OAuth client for provider."""
        return self.providers.get(provider_name)

    def get_authorization_url(
        self,
        provider_name: str,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> str:
        """Get authorization URL for provider."""
        client = self.get_provider(provider_name)
        if not client:
            raise ValueError(f"OAuth provider not configured: {provider_name}")

        return client.get_authorization_url(redirect_uri, state)

    async def authenticate(
        self,
        provider_name: str,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Authenticate with OAuth provider."""
        client = self.get_provider(provider_name)
        if not client:
            raise ValueError(f"OAuth provider not configured: {provider_name}")

        return await client.authenticate(code, redirect_uri)


# Global OAuth manager
_oauth_manager = OAuthManager()


def get_oauth_manager() -> OAuthManager:
    """Get global OAuth manager instance."""
    return _oauth_manager
