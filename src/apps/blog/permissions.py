from enum import Enum, auto
from typing import Any

from django.contrib.auth.models import User
from rest_framework import permissions

from apps.common.permissions import PermissionChecker


class BlogPermission(str, Enum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> str:
        return f"blog.{name.lower()}"

    VIEW_POST = auto()
    CREATE_POST = auto()
    EDIT_POST = auto()
    DELETE_POST = auto()
    PUBLISH_POST = auto()
    EDIT_ANY_POST = auto()
    DELETE_ANY_POST = auto()


PERMISSION_VERBOSE = {
    BlogPermission.VIEW_POST: "Can view post",
    BlogPermission.CREATE_POST: "Can create post",
    BlogPermission.EDIT_POST: "Can edit post",
    BlogPermission.DELETE_POST: "Can delete post",
    BlogPermission.PUBLISH_POST: "Can publish post",
    BlogPermission.EDIT_ANY_POST: "Can edit any post",
    BlogPermission.DELETE_ANY_POST: "Can delete any post",
}

PERMISSIONS = [
    (perm.value.replace("blog.", "", 1), PERMISSION_VERBOSE[perm])
    for perm in BlogPermission
]


class BlogPermissionChecker(PermissionChecker):
    def check_permission(self, user: User, permission: str) -> bool:
        if not user or not user.is_authenticated:
            return permission == "view_post"

        if permission == "view_post":
            return True

        elif permission == "create_post":
            return user.is_authenticated

        elif permission in ["edit_post", "delete_post", "publish_post"]:
            return user.is_authenticated

        elif permission == "edit_any_post":
            return user.is_staff or user.is_superuser

        elif permission == "delete_any_post":
            return user.is_superuser

        return False

    def get_supported_permissions(self) -> list[str]:
        return [permission.value for permission in BlogPermission]


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has an `author` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user
