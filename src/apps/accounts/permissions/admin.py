from rest_framework import permissions

from apps.common.exceptions import PermissionDeniedException


class IsAdmin(permissions.BasePermission):
    message = "Требуется роль администратора"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.has_role("admin"):
            return True

        raise PermissionDeniedException(
            message="Требуется роль администратора",
            errors=[{"code": "admin_required", "detail": "Требуется роль администратора"}],
        )

