from apps.accounts.views.admin import (
    PermissionDetailView,
    PermissionListView,
    RoleDetailView,
    RoleListView,
    RolePermissionDetailView,
    RolePermissionListView,
    UserListView,
    UserRoleDetailView,
    UserRoleListView,
)
from apps.accounts.views.auth import (
    LoginView,
    LogoutView,
    RefreshTokenView,
    RegisterView,
)
from apps.accounts.views.rbac import PermissionCheckView
from apps.accounts.views.user import UserProfileView

__all__ = [
    "PermissionCheckView",
    "RegisterView",
    "LoginView",
    "RefreshTokenView",
    "LogoutView",
    "UserProfileView",
    "RoleListView",
    "RoleDetailView",
    "PermissionListView",
    "PermissionDetailView",
    "RolePermissionListView",
    "RolePermissionDetailView",
    "UserListView",
    "UserRoleListView",
    "UserRoleDetailView",
]

