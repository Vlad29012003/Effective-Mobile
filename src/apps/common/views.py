"""
Permission checking API (Capabilities API) and common views.
"""

from django.http import JsonResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import permission_service
from .serializers import (
    HealthCheckResponseSerializer,
    PermissionCheckRequestSerializer,
    PermissionCheckResponseSerializer,
)


@extend_schema(tags=["permissions"])
class PermissionCheckView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Check multiple permissions",
        description="Check multiple permissions for the current user",
        request=PermissionCheckRequestSerializer,
        responses={200: PermissionCheckResponseSerializer},
    )
    def post(self, request):
        serializer = PermissionCheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actions = serializer.validated_data["actions"]

        result = permission_service.check_permissions(
            user=request.user, actions=actions
        )

        return Response(result, status=status.HTTP_200_OK)


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
    """
    Function for testing error handling.
    """
    if request.GET.get("type") == "500":
        raise Exception("Test server error")
    elif request.GET.get("type") == "404":
        from django.http import Http404

        raise Http404("Test not found error")
    else:
        from apps.common.exceptions import ValidationException

        raise ValidationException("Test validation error")
