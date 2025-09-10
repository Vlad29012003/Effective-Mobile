"""
Serializers for common application.
"""

from rest_framework import serializers


class PermissionCheckRequestSerializer(serializers.Serializer):
    """
    Serializer for permission check request.
    """

    actions = serializers.ListField(
        child=serializers.CharField(max_length=100),
        help_text="List of actions to check (e.g.: ['blog.create_post', 'blog.edit_post'])",
    )

    def validate_actions(self, value: list[str]) -> list[str]:
        """Validation of actions list."""
        if not value:
            raise serializers.ValidationError("Actions list cannot be empty")

        # Check actions format (should be module.action)
        for action in value:
            if "." not in action:
                raise serializers.ValidationError(
                    f"Invalid action format: '{action}'. Expected format: 'module.action'"
                )

        return value


class PermissionCheckResponseSerializer(serializers.Serializer):
    """
    Serializer for permission check response.

    Dynamic serializer that shows example response in documentation.
    """

    def to_representation(self, instance):
        """
        Returns dictionary {action: bool}.
        """
        # This is only used for OpenAPI documentation
        return {
            "blog.create_post": True,
            "blog.edit_post": False,
            "blog.delete_post": False,
            "user.view_profile": True,
        }


class HealthCheckResponseSerializer(serializers.Serializer):
    """
    Serializer for health check response.
    """

    status = serializers.CharField(help_text="Application status")
    service = serializers.CharField(help_text="Service name")
