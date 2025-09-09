"""
API для проверки разрешений (Capabilities API) и общие views.
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
    """
    API для проверки разрешений согласно стандарту Capabilities API.

    Фронтенд может запросить проверку множества разрешений за один запрос.
    Возвращает результат в формате {action: bool}.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Проверить разрешения пользователя",
        description="""
        Проверяет разрешения текущего пользователя для списка действий.

        Пример запроса:
        ```json
        {
          "actions": ["blog.create_post", "blog.edit_post"],
          "context": {"post_author_id": 123}  // опционально
        }
        ```

        Пример ответа:
        ```json
        {
          "blog.create_post": true,
          "blog.edit_post": false
        }
        ```
        """,
        request=PermissionCheckRequestSerializer,
        responses={200: PermissionCheckResponseSerializer},
        parameters=[
            OpenApiParameter(
                name="actions",
                description="Список действий для проверки",
                required=True,
                type=OpenApiTypes.OBJECT,
            )
        ],
    )
    def post(self, request):
        """
        Проверить разрешения для списка действий.
        """
        serializer = PermissionCheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actions = serializer.validated_data["actions"]
        context = serializer.validated_data.get("context", {})

        # Проверяем разрешения
        result = permission_service.check_permissions(
            user=request.user, actions=actions, context=context
        )

        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["permissions"])
class SinglePermissionCheckView(APIView):
    """
    API для проверки одного разрешения (упрощенный вариант).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Проверить одно разрешение",
        description="Проверяет одно разрешение для текущего пользователя",
        responses={200: PermissionCheckResponseSerializer},
        parameters=[
            OpenApiParameter(
                name="action",
                description="Действие для проверки (например: blog.create_post)",
                required=True,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="post_author_id",
                description="ID автора поста (для контекста)",
                required=False,
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="user_id",
                description="ID пользователя (для контекста)",
                required=False,
                type=OpenApiTypes.INT,
            ),
        ],
    )
    def get(self, request):
        """
        Проверить одно разрешение через GET параметры.
        """
        action = request.query_params.get("action")
        if not action:
            return Response(
                {"error": "Parameter 'action' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Собираем контекст из параметров запроса
        context = {}
        if request.query_params.get("post_author_id"):
            context["post_author_id"] = int(request.query_params["post_author_id"])
        if request.query_params.get("user_id"):
            context["user_id"] = int(request.query_params["user_id"])

        # Проверяем разрешение
        has_permission = permission_service.check_single_permission(
            user=request.user, action=action, context=context
        )

        return Response({action: has_permission}, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    """
    Health check endpoint для мониторинга состояния приложения.
    """

    permission_classes = []

    @extend_schema(
        tags=["health"],
        summary="Проверка состояния приложения",
        description="Возвращает статус работы приложения",
        responses={200: HealthCheckResponseSerializer},
    )
    def get(self, request):
        """Проверка здоровья приложения."""
        return JsonResponse({"status": "healthy", "service": "django-blog-template"})


def trigger_error(request):
    """
    Функция для тестирования обработки ошибок.
    """
    if request.GET.get("type") == "500":
        raise Exception("Test server error")
    elif request.GET.get("type") == "404":
        from django.http import Http404

        raise Http404("Test not found error")
    else:
        from apps.common.exceptions import ValidationException

        raise ValidationException("Test validation error")
