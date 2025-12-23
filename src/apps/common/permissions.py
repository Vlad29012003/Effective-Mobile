
import importlib
from abc import ABC, abstractmethod

from django.apps import apps
from django.contrib.auth.models import User


class PermissionChecker(ABC):
    @abstractmethod
    def check_permission(self, user: User, permission: str) -> bool:
    @abstractmethod
    def get_supported_permissions(self) -> list[str]:
        
class PermissionService:
    def __init__(self):
        self.checkers: dict[str, PermissionChecker] = {}
        self._discover_checkers()

    def _discover_checkers(self):
        for app_config in apps.get_app_configs():
            try:
                permissions_module = importlib.import_module(f"{app_config.name}.permissions")

                for attr_name in dir(permissions_module):
                    attr = getattr(permissions_module, attr_name)

                    if isinstance(attr, type) and issubclass(attr, PermissionChecker) and attr != PermissionChecker:
                        app_name = app_config.name.split(".")[-1]  # get last part (blog, user, etc.)
                        self.checkers[app_name] = attr()

            except (ImportError, AttributeError):
                continue

    def check_permissions(self, user: User, actions: list[str]) -> dict[str, bool]:
        result = {}

        for action in actions:
            result[action] = self.check_single_permission(user, action)

        return result

    def check_single_permission(self, user: User, action: str) -> bool:
        parts = action.split(".", 1)
        if len(parts) != 2:
            return False

        app_name, permission = parts
        checker = self.checkers.get(app_name)

        if not checker:
            return False

        return checker.check_permission(user, permission)

    def has_permission(self, user: User, action: str) -> bool:
        return self.check_single_permission(user, action)

    def get_registered_checkers(self) -> dict[str, PermissionChecker]:
        """Get list of registered checkers."""
        return self.checkers.copy()


permission_service = PermissionService()


def has_permission(user: User, action: str) -> bool:
    return permission_service.has_permission(user, action)


def check_permissions(user: User, actions: list[str]) -> dict[str, bool]:
    return permission_service.check_permissions(user, actions)
