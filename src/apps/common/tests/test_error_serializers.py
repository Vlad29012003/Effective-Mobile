"""
Test serializers specifically for error handling tests.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class TestValidationSerializer(serializers.Serializer):
    """Test serializer to trigger various validation errors."""

    email = serializers.EmailField(required=True)
    age = serializers.IntegerField(min_value=0, max_value=120)
    password = serializers.CharField(min_length=8, max_length=50)
    username = serializers.CharField(required=True, max_length=30)

    def validate_email(self, value):
        """Custom email validation."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.", code="duplicate")
        return value

    def validate_username(self, value):
        """Custom username validation."""
        if len(value.strip()) == 0:
            raise serializers.ValidationError("Username cannot be empty.", code="blank")
        return value

    def validate(self, data):
        """Cross-field validation."""
        if data.get("username") == data.get("email"):
            raise serializers.ValidationError({"username": "Username and email cannot be the same."})
        return data


class TestBusinessLogicSerializer(serializers.Serializer):
    """Test serializer for business logic errors."""

    title = serializers.CharField(required=True, max_length=100)
    content = serializers.CharField(required=True)
    is_published = serializers.BooleanField(default=False)

    def validate_title(self, value):
        """Business rule: certain words are forbidden."""
        forbidden_words = ["spam", "forbidden", "banned"]
        if any(word in value.lower() for word in forbidden_words):
            raise serializers.ValidationError("Title contains forbidden words.", code="forbidden_content")
        return value

    def validate(self, data):
        """Business rule: published posts must have substantial content."""
        if data.get("is_published") and len(data.get("content", "").strip()) < 50:
            raise serializers.ValidationError(
                {
                    "content": "Published posts must have at least 50 characters.",
                    "is_published": "Cannot publish posts with insufficient content.",
                }
            )
        return data
