"""
Сериализаторы для common приложения.
"""

from rest_framework import serializers


class PermissionCheckRequestSerializer(serializers.Serializer):
    """
    Сериализатор для запроса проверки разрешений.
    """

    actions = serializers.ListField(
        child=serializers.CharField(max_length=100),
        help_text="Список действий для проверки (например: ['blog.create_post', 'blog.edit_post'])",
    )
    context = serializers.DictField(
        required=False,
        help_text="Дополнительный контекст для проверки разрешений (например: {'post_author_id': 123})",
    )

    def validate_actions(self, value: list[str]) -> list[str]:
        """Валидация списка действий."""
        if not value:
            raise serializers.ValidationError("Actions list cannot be empty")

        # Проверяем формат действий (должен быть module.action)
        for action in value:
            if "." not in action:
                raise serializers.ValidationError(
                    f"Invalid action format: '{action}'. Expected format: 'module.action'"
                )

        return value


class PermissionCheckResponseSerializer(serializers.Serializer):
    """
    Сериализатор для ответа проверки разрешений.

    Динамический сериализатор, который показывает пример ответа в документации.
    """

    def to_representation(self, instance):
        """
        Возвращает словарь {action: bool}.
        """
        # Это используется только для документации OpenAPI
        return {
            "blog.create_post": True,
            "blog.edit_post": False,
            "blog.delete_post": False,
            "user.view_profile": True,
        }


class PostContextSerializer(serializers.Serializer):
    """
    Контекст для проверки разрешений связанных с постами.
    """

    post_author_id = serializers.IntegerField(
        required=False, help_text="ID автора поста для проверки разрешений"
    )


class UserContextSerializer(serializers.Serializer):
    """
    Контекст для проверки разрешений связанных с пользователями.
    """

    user_id = serializers.IntegerField(
        required=False, help_text="ID пользователя для проверки разрешений"
    )


class HealthCheckResponseSerializer(serializers.Serializer):
    """
    Сериализатор для ответа health check.
    """

    status = serializers.CharField(help_text="Статус работы приложения")
    service = serializers.CharField(help_text="Название сервиса")
