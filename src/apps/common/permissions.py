from django.contrib.auth import get_user_model

from apps.accounts.models.rbac import Permission, RolePermission, UserRole
from apps.accounts.models.object_permission import RoleObjectPermission, UserObjectPermission

User = get_user_model()


def has_permission(user: User, permission_code: str) -> bool:
    if not user or not user.is_active or user.is_deleted:
        return False

    try:
        permission_obj = Permission.objects.get(code=permission_code)
    except Permission.DoesNotExist:
        return False

    user_roles = UserRole.objects.filter(user=user).select_related("role")
    role_ids = [ur.role_id for ur in user_roles]

    if not role_ids:
        return False

    has_role_permission = RolePermission.objects.filter(
        role_id__in=role_ids,
        permission=permission_obj
    ).exists()

    return has_role_permission


def check_permissions(user: User, permission_codes: list[str]) -> dict[str, bool]:
    result = {}
    for permission_code in permission_codes:
        result[permission_code] = has_permission(user, permission_code)
    return result


def check_object_permission(
    user: User,
    permission_code: str,
    resource_type: str,
    resource_id: int
) -> bool | None:
    if not user or not user.is_active or user.is_deleted:
        return False

    try:
        permission_obj = Permission.objects.get(code=permission_code)
    except Permission.DoesNotExist:
        return None

    user_obj_perm = UserObjectPermission.objects.filter(
        user=user,
        permission=permission_obj,
        resource_type=resource_type,
        resource_id=resource_id
    ).first()

    if user_obj_perm:
        return user_obj_perm.is_granted

    user_roles = UserRole.objects.filter(user=user).select_related("role")
    role_ids = [ur.role_id for ur in user_roles]

    if role_ids:
        role_obj_perm = RoleObjectPermission.objects.filter(
            role_id__in=role_ids,
            permission=permission_obj,
            resource_type=resource_type,
            resource_id=resource_id
        ).first()

        if role_obj_perm:
            return role_obj_perm.is_granted

    return None


def has_object_permission(
    user: User,
    permission_code: str,
    resource_type: str,
    resource_id: int
) -> bool:
    obj_permission = check_object_permission(user, permission_code, resource_type, resource_id)
    
    if obj_permission is not None:
        return obj_permission
    
    return has_permission(user, permission_code)
