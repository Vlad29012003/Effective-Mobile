from rest_framework import permissions

from apps.common.exceptions import PermissionDeniedException
from apps.common.permissions import has_object_permission, has_permission


class HasPermission(permissions.BasePermission):
    message = "У вас нет прав для выполнения этого действия"

    METHOD_TO_ACTION = {
        "GET": "read",
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
    }

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        permission_code = self._get_permission_code(request, view)
        if not permission_code:
            return False

        has_perm = has_permission(request.user, permission_code)

        if not has_perm:
            self.message = f"Требуется право: {permission_code}"

        return has_perm

    def _get_permission_code(self, request, view):
        if hasattr(view, "get_required_permission"):
            return view.get_required_permission(request)

        if hasattr(view, "required_permission"):
            return view.required_permission

        if hasattr(view, "resource_type"):
            action = self.METHOD_TO_ACTION.get(request.method)
            if action:
                return f"{view.resource_type}.{action}"

        return None


class HasObjectPermission(permissions.BasePermission):

    message = "У вас нет прав для доступа к этому ресурсу"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        permission_code = self._get_permission_code(request, view)
        resource_type = self._get_resource_type(request, view)

        if not permission_code or not resource_type:
            return False

        resource_id = getattr(obj, "id", None) or getattr(obj, "pk", None)

        if resource_id is None:
            return False

        if has_object_permission(request.user, permission_code, resource_type, resource_id):
            return True

        self.message = f"Требуется право: {permission_code} для {resource_type}#{resource_id}"
        raise PermissionDeniedException(
            message="У вас нет прав для доступа к этому ресурсу",
            errors=[
                {
                    "code": "permission_denied",
                    "detail": f"Требуется право: {permission_code} для {resource_type}#{resource_id}",
                }
            ],
        )

    def _get_permission_code(self, request, view):
        if hasattr(view, "get_required_permission"):
            return view.get_required_permission(request)
        return getattr(view, "required_permission", None)

    def _get_resource_type(self, request, view):
        if hasattr(view, "get_resource_type"):
            return view.get_resource_type(request)
        return getattr(view, "resource_type", None)

