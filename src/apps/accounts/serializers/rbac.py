from rest_framework import serializers


class PermissionCheckRequestSerializer(serializers.Serializer):

    actions = serializers.ListField(
        child=serializers.CharField(max_length=200),
        help_text="List of permission codes to check (e.g.: ['blog.post.create', 'blog.post.update'])",
    )

    def validate_actions(self, value: list[str]) -> list[str]:
        if not value:
            raise serializers.ValidationError("Actions list cannot be empty")

        for action in value:
            if "." not in action:
                raise serializers.ValidationError(
                    f"Invalid action format: '{action}'. Expected format: 'module.action'"
                )

        return value

