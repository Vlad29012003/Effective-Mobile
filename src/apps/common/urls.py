"""
URLs для common приложения.
"""

from django.urls import path

from .views import HealthCheckView, PermissionCheckView, trigger_error

app_name = "common"

urlpatterns = [
    # Capabilities API для проверки разрешений
    path("permissions/check/", PermissionCheckView.as_view(), name="permission-check"),
    # Health check
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("trigger-error/", trigger_error, name="trigger-error"),
]
