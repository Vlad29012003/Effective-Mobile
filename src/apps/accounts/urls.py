from django.urls import path

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
]
