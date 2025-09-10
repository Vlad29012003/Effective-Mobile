from django.urls import path

from apps.accounts.views import LoginView, PermissionCheckView

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("permissions/check/", PermissionCheckView.as_view(), name="permission-check"),
]
