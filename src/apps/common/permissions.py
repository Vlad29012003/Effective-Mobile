"""
Система permissions с декларативной моделью (Capabilities API).
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from django.contrib.auth.models import User


class Permission(Enum):
    """Перечисление всех доступных разрешений в системе."""

    # Blog permissions
    BLOG_VIEW_POST = "blog.view_post"
    BLOG_CREATE_POST = "blog.create_post"
    BLOG_EDIT_POST = "blog.edit_post"
    BLOG_DELETE_POST = "blog.delete_post"
    BLOG_PUBLISH_POST = "blog.publish_post"
    BLOG_EDIT_ANY_POST = "blog.edit_any_post"
    BLOG_DELETE_ANY_POST = "blog.delete_any_post"

    # User permissions
    USER_VIEW_PROFILE = "user.view_profile"
    USER_EDIT_PROFILE = "user.edit_profile"
    USER_VIEW_ANY_PROFILE = "user.view_any_profile"

    # Admin permissions
    ADMIN_MANAGE_USERS = "admin.manage_users"
    ADMIN_VIEW_ANALYTICS = "admin.view_analytics"


class PermissionChecker(ABC):
    """Абстрактный класс для проверки разрешений."""

    @abstractmethod
    def check_permission(
        self, user: User, permission: str, context: dict[str, Any] = None
    ) -> bool:
        """
        Проверить, есть ли у пользователя разрешение.

        Args:
            user: Пользователь
            permission: Название разрешения
            context: Дополнительный контекст (например, ID поста)

        Returns:
            True если разрешение есть, False иначе
        """


class BlogPermissionChecker(PermissionChecker):
    """Проверка разрешений для блога."""

    def check_permission(
        self, user: User, permission: str, context: dict[str, Any] = None
    ) -> bool:
        if not user.is_authenticated:
            return permission in [Permission.BLOG_VIEW_POST.value]

        context = context or {}

        if permission == Permission.BLOG_VIEW_POST.value:
            return True

        elif permission == Permission.BLOG_CREATE_POST.value:
            return user.is_authenticated

        elif permission == Permission.BLOG_EDIT_POST.value:
            post_author_id = context.get("post_author_id")
            return user.is_authenticated and (
                user.id == post_author_id or user.is_superuser
            )

        elif permission == Permission.BLOG_DELETE_POST.value:
            post_author_id = context.get("post_author_id")
            return user.is_authenticated and (
                user.id == post_author_id or user.is_superuser
            )

        elif permission == Permission.BLOG_PUBLISH_POST.value:
            post_author_id = context.get("post_author_id")
            return user.is_authenticated and (
                user.id == post_author_id or user.is_superuser
            )

        elif permission == Permission.BLOG_EDIT_ANY_POST.value:
            return user.is_staff or user.is_superuser

        elif permission == Permission.BLOG_DELETE_ANY_POST.value:
            return user.is_superuser

        return False


class UserPermissionChecker(PermissionChecker):
    """Проверка разрешений для пользователей."""

    def check_permission(
        self, user: User, permission: str, context: dict[str, Any] = None
    ) -> bool:
        if not user.is_authenticated:
            return False

        context = context or {}

        if permission == Permission.USER_VIEW_PROFILE.value:
            return True

        elif permission == Permission.USER_EDIT_PROFILE.value:
            target_user_id = context.get("user_id")
            return user.id == target_user_id or user.is_superuser

        elif permission == Permission.USER_VIEW_ANY_PROFILE.value:
            return user.is_staff or user.is_superuser

        return False


class AdminPermissionChecker(PermissionChecker):
    """Проверка разрешений для администрирования."""

    def check_permission(
        self, user: User, permission: str, context: dict[str, Any] = None
    ) -> bool:
        if permission == Permission.ADMIN_MANAGE_USERS.value:
            return user.is_superuser

        elif permission == Permission.ADMIN_VIEW_ANALYTICS.value:
            return user.is_staff or user.is_superuser

        return False


class PermissionService:
    """Сервис для проверки разрешений."""

    def __init__(self):
        self.checkers = {
            "blog": BlogPermissionChecker(),
            "user": UserPermissionChecker(),
            "admin": AdminPermissionChecker(),
        }

    def check_permissions(
        self, user: User, actions: list[str], context: dict[str, Any] = None
    ) -> dict[str, bool]:
        """
        Проверить множество разрешений одновременно.

        Args:
            user: Пользователь
            actions: Список действий для проверки
            context: Контекст для проверки

        Returns:
            Словарь {action: bool}
        """
        result = {}

        for action in actions:
            result[action] = self.check_single_permission(user, action, context)

        return result

    def check_single_permission(
        self, user: User, action: str, context: dict[str, Any] = None
    ) -> bool:
        """
        Проверить одно разрешение.

        Args:
            user: Пользователь
            action: Действие для проверки (например, "blog.create_post")
            context: Контекст для проверки

        Returns:
            True если разрешение есть, False иначе
        """
        # Извлекаем модуль из действия (blog.create_post -> blog)
        parts = action.split(".", 1)
        if len(parts) != 2:
            return False

        module, permission = parts
        checker = self.checkers.get(module)

        if not checker:
            return False

        return checker.check_permission(user, action, context)

    def has_permission(self, user: User, action: str, **context_kwargs) -> bool:
        """
        Удобный метод для проверки одного разрешения.

        Args:
            user: Пользователь
            action: Действие для проверки
            **context_kwargs: Контекст как именованные параметры

        Returns:
            True если разрешение есть, False иначе
        """
        return self.check_single_permission(user, action, context_kwargs)


# Глобальный экземпляр сервиса
permission_service = PermissionService()


def has_permission(user: User, action: str, **context) -> bool:
    """
    Глобальная функция для проверки разрешения.

    Args:
        user: Пользователь
        action: Действие для проверки
        **context: Контекст

    Returns:
        True если разрешение есть, False иначе
    """
    return permission_service.has_permission(user, action, **context)


def check_permissions(user: User, actions: list[str], **context) -> dict[str, bool]:
    """
    Глобальная функция для проверки множества разрешений.

    Args:
        user: Пользователь
        actions: Список действий
        **context: Контекст

    Returns:
        Словарь {action: bool}
    """
    return permission_service.check_permissions(user, actions, context)
