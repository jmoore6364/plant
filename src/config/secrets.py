"""
Secrets management integration.

Supports multiple secret backends:
- Environment variables
- HashiCorp Vault
- AWS Secrets Manager
- File-based secrets
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SecretBackend(ABC):
    """Abstract base class for secret backends."""

    @abstractmethod
    def get_secret(self, path: str) -> Optional[str]:
        """Get a secret by path."""
        pass

    @abstractmethod
    def set_secret(self, path: str, value: str) -> bool:
        """Set a secret."""
        pass


class EnvironmentSecretBackend(SecretBackend):
    """Get secrets from environment variables."""

    def get_secret(self, path: str) -> Optional[str]:
        """Get secret from environment variable."""
        # Convert path to env var name (e.g., "database/password" -> "DATABASE_PASSWORD")
        env_name = path.upper().replace("/", "_").replace("-", "_")
        return os.getenv(env_name)

    def set_secret(self, path: str, value: str) -> bool:
        """Set environment variable (runtime only)."""
        env_name = path.upper().replace("/", "_").replace("-", "_")
        os.environ[env_name] = value
        return True


class FileSecretBackend(SecretBackend):
    """Get secrets from JSON file."""

    def __init__(self, secrets_file: str = "secrets.json"):
        self.secrets_file = Path(secrets_file)
        self._cache: Optional[Dict[str, Any]] = None

    def _load_secrets(self) -> Dict[str, Any]:
        """Load secrets from file."""
        if not self.secrets_file.exists():
            logger.warning(f"Secrets file not found: {self.secrets_file}")
            return {}

        try:
            with open(self.secrets_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading secrets file: {e}")
            return {}

    def get_secret(self, path: str) -> Optional[str]:
        """Get secret from file."""
        if self._cache is None:
            self._cache = self._load_secrets()

        # Navigate nested dict using path
        parts = path.split("/")
        current = self._cache

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return str(current) if current is not None else None

    def set_secret(self, path: str, value: str) -> bool:
        """Set secret in file."""
        secrets = self._load_secrets()

        # Navigate and create nested structure
        parts = path.split("/")
        current = secrets

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

        # Write back to file
        try:
            with open(self.secrets_file, 'w') as f:
                json.dump(secrets, f, indent=2)
            self._cache = secrets
            return True
        except Exception as e:
            logger.error(f"Error writing secrets file: {e}")
            return False


class VaultSecretBackend(SecretBackend):
    """Get secrets from HashiCorp Vault."""

    def __init__(
        self,
        vault_addr: Optional[str] = None,
        vault_token: Optional[str] = None,
        mount_point: str = "secret"
    ):
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR", "http://localhost:8200")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.mount_point = mount_point

        self.client = None
        if self.vault_token:
            try:
                import hvac
                self.client = hvac.Client(
                    url=self.vault_addr,
                    token=self.vault_token
                )
                if not self.client.is_authenticated():
                    logger.warning("Vault authentication failed")
                    self.client = None
            except ImportError:
                logger.warning("hvac library not installed, Vault backend disabled")
            except Exception as e:
                logger.error(f"Error initializing Vault client: {e}")

    def get_secret(self, path: str) -> Optional[str]:
        """Get secret from Vault."""
        if not self.client:
            return None

        try:
            # Read secret from Vault
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point
            )

            # Extract value from response
            data = response.get("data", {}).get("data", {})

            # If path contains a key (e.g., "database/postgres:password")
            if ":" in path:
                secret_path, key = path.rsplit(":", 1)
                return data.get(key)
            else:
                # Return the first value if only one key exists
                if len(data) == 1:
                    return list(data.values())[0]
                # Return JSON string if multiple keys
                return json.dumps(data)

        except Exception as e:
            logger.error(f"Error reading secret from Vault: {e}")
            return None

    def set_secret(self, path: str, value: str) -> bool:
        """Set secret in Vault."""
        if not self.client:
            return False

        try:
            # Parse path and key if provided
            if ":" in path:
                secret_path, key = path.rsplit(":", 1)
                data = {key: value}
            else:
                secret_path = path
                data = {"value": value}

            # Write secret to Vault
            self.client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret=data,
                mount_point=self.mount_point
            )
            return True

        except Exception as e:
            logger.error(f"Error writing secret to Vault: {e}")
            return False


class AWSSecretsManagerBackend(SecretBackend):
    """Get secrets from AWS Secrets Manager."""

    def __init__(self, region_name: Optional[str] = None):
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.client = None

        try:
            import boto3
            self.client = boto3.client(
                'secretsmanager',
                region_name=self.region_name
            )
        except ImportError:
            logger.warning("boto3 library not installed, AWS Secrets Manager backend disabled")
        except Exception as e:
            logger.error(f"Error initializing AWS Secrets Manager client: {e}")

    def get_secret(self, path: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        if not self.client:
            return None

        try:
            response = self.client.get_secret_value(SecretId=path)

            # Return secret string
            if 'SecretString' in response:
                secret = response['SecretString']

                # If path contains a key (e.g., "my-secret:password")
                if ":" in path:
                    _, key = path.rsplit(":", 1)
                    try:
                        secret_dict = json.loads(secret)
                        return secret_dict.get(key)
                    except json.JSONDecodeError:
                        return secret
                return secret
            else:
                # Binary secret
                import base64
                return base64.b64decode(response['SecretBinary']).decode('utf-8')

        except Exception as e:
            logger.error(f"Error reading secret from AWS Secrets Manager: {e}")
            return None

    def set_secret(self, path: str, value: str) -> bool:
        """Set secret in AWS Secrets Manager."""
        if not self.client:
            return False

        try:
            # Try to update existing secret
            try:
                self.client.update_secret(
                    SecretId=path,
                    SecretString=value
                )
            except self.client.exceptions.ResourceNotFoundException:
                # Create new secret if doesn't exist
                self.client.create_secret(
                    Name=path,
                    SecretString=value
                )

            return True

        except Exception as e:
            logger.error(f"Error writing secret to AWS Secrets Manager: {e}")
            return False


class SecretsManager:
    """Manage secrets from multiple backends with fallback."""

    def __init__(self, backends: Optional[list] = None):
        """
        Initialize secrets manager with backends.

        Args:
            backends: List of backend names to use. If None, uses all available.
                     Tries backends in order until secret is found.
        """
        self.backends: list[SecretBackend] = []

        # Default backend order
        if backends is None:
            backends = ["env", "file", "vault", "aws"]

        # Initialize backends
        for backend_name in backends:
            backend = self._create_backend(backend_name)
            if backend:
                self.backends.append(backend)

        if not self.backends:
            logger.warning("No secret backends initialized, using environment only")
            self.backends = [EnvironmentSecretBackend()]

    def _create_backend(self, name: str) -> Optional[SecretBackend]:
        """Create a secret backend by name."""
        try:
            if name == "env":
                return EnvironmentSecretBackend()
            elif name == "file":
                return FileSecretBackend()
            elif name == "vault":
                return VaultSecretBackend()
            elif name == "aws":
                return AWSSecretsManagerBackend()
            else:
                logger.warning(f"Unknown secret backend: {name}")
                return None
        except Exception as e:
            logger.error(f"Error creating {name} backend: {e}")
            return None

    def get_secret(self, path: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret from backends (tries in order).

        Args:
            path: Secret path
            default: Default value if secret not found

        Returns:
            Secret value or default
        """
        for backend in self.backends:
            try:
                value = backend.get_secret(path)
                if value is not None:
                    logger.debug(f"Secret '{path}' found in {backend.__class__.__name__}")
                    return value
            except Exception as e:
                logger.error(f"Error getting secret from {backend.__class__.__name__}: {e}")

        logger.debug(f"Secret '{path}' not found in any backend, using default")
        return default

    def set_secret(self, path: str, value: str, backend: Optional[str] = None) -> bool:
        """
        Set secret in specified backend or first available.

        Args:
            path: Secret path
            value: Secret value
            backend: Backend name (optional)

        Returns:
            True if successful
        """
        backends_to_try = self.backends

        if backend:
            # Find specific backend
            backends_to_try = [
                b for b in self.backends
                if b.__class__.__name__.lower().startswith(backend.lower())
            ]

        for backend in backends_to_try:
            try:
                if backend.set_secret(path, value):
                    logger.info(f"Secret '{path}' set in {backend.__class__.__name__}")
                    return True
            except Exception as e:
                logger.error(f"Error setting secret in {backend.__class__.__name__}: {e}")

        logger.error(f"Failed to set secret '{path}' in any backend")
        return False
