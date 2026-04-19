"""Authentication and authorization."""

import hashlib
import secrets
import time
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class APIKey(BaseModel):
    """API key model."""
    key: str = Field(..., description="API key")
    name: str = Field(..., description="Key name")
    user_id: str = Field(..., description="User ID")
    permissions: List[str] = Field(default_factory=list, description="Permissions")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp")
    expires_at: Optional[float] = Field(None, description="Expiration timestamp")
    is_active: bool = Field(True, description="Whether key is active")
    rate_limit: Optional[int] = Field(None, description="Custom rate limit")


class User(BaseModel):
    """User model."""
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="Email address")
    roles: List[str] = Field(default_factory=list, description="User roles")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    is_active: bool = Field(True, description="Whether user is active")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")


class AuthManager:
    """Manage authentication and authorization."""

    def __init__(self):
        """Initialize auth manager."""
        self._api_keys: Dict[str, APIKey] = {}
        self._users: Dict[str, User] = {}
        self._role_permissions: Dict[str, Set[str]] = {
            "admin": {"*"},  # All permissions
            "user": {"read", "write"},
            "readonly": {"read"},
        }

    def generate_api_key(
        self,
        user_id: str,
        name: str,
        permissions: Optional[List[str]] = None,
        expires_in: Optional[float] = None
    ) -> str:
        """Generate a new API key.

        Args:
            user_id: User ID
            name: Key name
            permissions: List of permissions
            expires_in: Expiration time in seconds

        Returns:
            Generated API key
        """
        # Generate secure random key
        key = f"am_{secrets.token_urlsafe(32)}"

        # Calculate expiration
        expires_at = None
        if expires_in:
            expires_at = time.time() + expires_in

        # Create API key object
        api_key = APIKey(
            key=key,
            name=name,
            user_id=user_id,
            permissions=permissions or [],
            expires_at=expires_at
        )

        self._api_keys[key] = api_key
        logger.info(f"Generated API key for user {user_id}: {name}")

        return key

    def validate_api_key(self, key: str) -> Optional[APIKey]:
        """Validate API key.

        Args:
            key: API key to validate

        Returns:
            APIKey object if valid, None otherwise
        """
        api_key = self._api_keys.get(key)

        if not api_key:
            logger.warning(f"Invalid API key: {key[:10]}...")
            return None

        if not api_key.is_active:
            logger.warning(f"Inactive API key: {api_key.name}")
            return None

        if api_key.expires_at and time.time() > api_key.expires_at:
            logger.warning(f"Expired API key: {api_key.name}")
            return None

        return api_key

    def revoke_api_key(self, key: str) -> bool:
        """Revoke an API key.

        Args:
            key: API key to revoke

        Returns:
            True if revoked successfully
        """
        if key in self._api_keys:
            self._api_keys[key].is_active = False
            logger.info(f"Revoked API key: {self._api_keys[key].name}")
            return True
        return False

    def delete_api_key(self, key: str) -> bool:
        """Delete an API key.

        Args:
            key: API key to delete

        Returns:
            True if deleted successfully
        """
        if key in self._api_keys:
            name = self._api_keys[key].name
            del self._api_keys[key]
            logger.info(f"Deleted API key: {name}")
            return True
        return False

    def list_api_keys(self, user_id: Optional[str] = None) -> List[APIKey]:
        """List API keys.

        Args:
            user_id: Filter by user ID

        Returns:
            List of API keys
        """
        keys = list(self._api_keys.values())
        if user_id:
            keys = [k for k in keys if k.user_id == user_id]
        return keys

    def create_user(
        self,
        user_id: str,
        username: str,
        email: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> User:
        """Create a new user.

        Args:
            user_id: User ID
            username: Username
            email: Email address
            roles: User roles

        Returns:
            Created user
        """
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            roles=roles or ["user"]
        )

        # Assign permissions based on roles
        permissions = set()
        for role in user.roles:
            permissions.update(self._role_permissions.get(role, set()))
        user.permissions = list(permissions)

        self._users[user_id] = user
        logger.info(f"Created user: {username} ({user_id})")

        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None
        """
        return self._users.get(user_id)

    def update_user_roles(self, user_id: str, roles: List[str]) -> bool:
        """Update user roles.

        Args:
            user_id: User ID
            roles: New roles

        Returns:
            True if updated successfully
        """
        user = self._users.get(user_id)
        if not user:
            return False

        user.roles = roles

        # Update permissions
        permissions = set()
        for role in roles:
            permissions.update(self._role_permissions.get(role, set()))
        user.permissions = list(permissions)

        logger.info(f"Updated roles for user {user_id}: {roles}")
        return True

    def check_permission(
        self,
        user_id: str,
        permission: str,
        api_key: Optional[str] = None
    ) -> bool:
        """Check if user has permission.

        Args:
            user_id: User ID
            permission: Permission to check
            api_key: Optional API key to check

        Returns:
            True if user has permission
        """
        # Check API key permissions first
        if api_key:
            key_obj = self.validate_api_key(api_key)
            if not key_obj:
                return False

            if "*" in key_obj.permissions or permission in key_obj.permissions:
                return True

        # Check user permissions
        user = self._users.get(user_id)
        if not user or not user.is_active:
            return False

        return "*" in user.permissions or permission in user.permissions

    def add_role(self, role: str, permissions: Set[str]) -> None:
        """Add a new role.

        Args:
            role: Role name
            permissions: Set of permissions
        """
        self._role_permissions[role] = permissions
        logger.info(f"Added role: {role} with permissions: {permissions}")

    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """Hash a password.

        Args:
            password: Plain text password
            salt: Optional salt (generated if not provided)

        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        )

        return hashed.hex(), salt

    def verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verify a password.

        Args:
            password: Plain text password
            hashed: Hashed password
            salt: Salt used for hashing

        Returns:
            True if password matches
        """
        new_hash, _ = self.hash_password(password, salt)
        return secrets.compare_digest(new_hash, hashed)

    def create_session_token(self, user_id: str, expires_in: float = 3600) -> str:
        """Create a session token.

        Args:
            user_id: User ID
            expires_in: Expiration time in seconds

        Returns:
            Session token
        """
        token = secrets.token_urlsafe(32)
        # In production, store this in a database with expiration
        return token

    def get_user_from_api_key(self, api_key: str) -> Optional[User]:
        """Get user from API key.

        Args:
            api_key: API key

        Returns:
            User object or None
        """
        key_obj = self.validate_api_key(api_key)
        if not key_obj:
            return None

        return self.get_user(key_obj.user_id)
