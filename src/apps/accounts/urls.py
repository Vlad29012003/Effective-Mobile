from django.urls import path

from apps.accounts.views.rbac import PermissionCheckView

urlpatterns = [
    path("permissions/check/", PermissionCheckView.as_view(), name="permission-check"),
]
