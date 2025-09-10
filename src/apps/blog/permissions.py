from enum import Enum

from django.contrib.auth.models import User
from rest_framework import permissions

from apps.common.permissions import PermissionChecker


class BlogPermission(Enum):
    VIEW_POST = "view_post"
    CREATE_POST = "create_post"
    EDIT_POST = "edit_post"
    DELETE_POST = "delete_post"
    PUBLISH_POST = "publish_post"
    EDIT_ANY_POST = "edit_any_post"
    DELETE_ANY_POST = "delete_any_post"


class BlogPermissionChecker(PermissionChecker):
    def check_permission(self, user: User, permission: str) -> bool:
        if not user or not user.is_authenticated:
            return permission == BlogPermission.VIEW_POST.value

        if permission == BlogPermission.VIEW_POST.value:
            return True

        elif permission == BlogPermission.CREATE_POST.value:
            return user.is_authenticated

        elif permission in [
            BlogPermission.EDIT_POST.value,
            BlogPermission.DELETE_POST.value,
            BlogPermission.PUBLISH_POST.value,
        ]:
            return user.is_authenticated

        elif permission == BlogPermission.EDIT_ANY_POST.value:
            return user.is_staff or user.is_superuser

        elif permission == BlogPermission.DELETE_ANY_POST.value:
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
