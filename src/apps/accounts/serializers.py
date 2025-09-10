from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


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

        for action in value:
            if "." not in action:
                raise serializers.ValidationError(
                    f"Invalid action format: '{action}'. Expected format: 'module.action'"
                )

        return value
