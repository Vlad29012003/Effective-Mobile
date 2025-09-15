"""
Common views for health checks and error testing.
"""

from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from .serializers import HealthCheckResponseSerializer


class HealthCheckView(APIView):
    """
    Health check endpoint for application monitoring.
    """

    permission_classes: list = []

    @extend_schema(
        tags=["health"],
        summary="Application health check",
        description="Returns application status",
        responses={200: HealthCheckResponseSerializer},
    )
    def get(self, request):
        """Application health check."""
        return JsonResponse({"status": "healthy", "service": "django-blog-template"})


def trigger_error(request):
    1 / 0
