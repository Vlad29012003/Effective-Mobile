from django.urls import path

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

app_name = "accounts"

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="refresh-token"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("users/me/", UserProfileView.as_view(), name="user-profile"),
    path("permissions/check/", PermissionCheckView.as_view(), name="permission-check"),
    path("admin/roles/", RoleListView.as_view(), name="admin-role-list"),
    path("admin/roles/<int:role_id>/", RoleDetailView.as_view(), name="admin-role-detail"),
    path("admin/permissions/", PermissionListView.as_view(), name="admin-permission-list"),
    path("admin/permissions/<int:permission_id>/", PermissionDetailView.as_view(), name="admin-permission-detail"),
    path("admin/roles/<int:role_id>/permissions/", RolePermissionListView.as_view(), name="admin-role-permission-list"),
    path("admin/roles/<int:role_id>/permissions/<int:permission_id>/", RolePermissionDetailView.as_view(), name="admin-role-permission-detail"),
    path("admin/users/", UserListView.as_view(), name="admin-user-list"),
    path("admin/users/<int:user_id>/roles/", UserRoleListView.as_view(), name="admin-user-role-list"),
    path("admin/users/<int:user_id>/roles/<int:role_id>/", UserRoleDetailView.as_view(), name="admin-user-role-detail"),
]
