"""
Base permission system with modular architecture.
"""

import importlib
from abc import ABC, abstractmethod

from django.apps import apps
from django.contrib.auth.models import User


class PermissionChecker(ABC):
    """Abstract base class for permission checking."""

    @abstractmethod
    def check_permission(self, user: User, permission: str) -> bool:
        """
        Check if user has permission.

        Args:
            user: User
            permission: Permission name (e.g., "view_post")

        Returns:
            True if permission exists, False otherwise
        """

    @abstractmethod
    def get_supported_permissions(self) -> list[str]:
        """
        Get list of supported permissions.

        Returns:
            List of permission names
        """


class PermissionService:
    """Service for permission checking with automatic checker discovery."""

    def __init__(self):
        self.checkers: dict[str, PermissionChecker] = {}
        self._discover_checkers()

    def _discover_checkers(self):
        """Automatically finds and registers permission checkers from all apps."""
        for app_config in apps.get_app_configs():
            try:
                # Try to import permissions module from each app
                permissions_module = importlib.import_module(
                    f"{app_config.name}.permissions"
                )

                # Look for PermissionChecker class in module
                for attr_name in dir(permissions_module):
                    attr = getattr(permissions_module, attr_name)

                    # Check if this is a PermissionChecker subclass
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, PermissionChecker)
                        and attr != PermissionChecker
                    ):
                        # Register checker
                        app_name = app_config.name.split(".")[
                            -1
                        ]  # get last part (blog, user, etc.)
                        self.checkers[app_name] = attr()

            except (ImportError, AttributeError):
                # If app has no permissions module or PermissionChecker - skip
                continue

    def check_permissions(self, user: User, actions: list[str]) -> dict[str, bool]:
        """
        Check multiple permissions at once.

        Args:
            user: User
            actions: List of actions to check (format: "app.permission")

        Returns:
            Dictionary {action: bool}
        """
        result = {}

        for action in actions:
            result[action] = self.check_single_permission(user, action)

        return result

    def check_single_permission(self, user: User, action: str) -> bool:
        """
        Check single permission.

        Args:
            user: User
            action: Action to check (e.g., "blog.view_post")

        Returns:
            True if permission exists, False otherwise
        """
        # Extract module from action (blog.view_post -> blog)
        parts = action.split(".", 1)
        if len(parts) != 2:
            return False

        app_name, permission = parts
        checker = self.checkers.get(app_name)

        if not checker:
            return False

        return checker.check_permission(user, permission)

    def has_permission(self, user: User, action: str) -> bool:
        """
        Convenient method for checking single permission.

        Args:
            user: User
            action: Action to check

        Returns:
            True if permission exists, False otherwise
        """
        return self.check_single_permission(user, action)

    def get_registered_checkers(self) -> dict[str, PermissionChecker]:
        """Get list of registered checkers."""
        return self.checkers.copy()


# Global service instance
permission_service = PermissionService()


def has_permission(user: User, action: str) -> bool:
    """
    Global function for permission checking.

    Args:
        user: User
        action: Action to check

    Returns:
        True if permission exists, False otherwise
    """
    return permission_service.has_permission(user, action)


def check_permissions(user: User, actions: list[str]) -> dict[str, bool]:
    """
    Global function for checking multiple permissions.

    Args:
        user: User
        actions: List of actions

    Returns:
        Dictionary {action: bool}
    """
    return permission_service.check_permissions(user, actions)
