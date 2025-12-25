from rest_framework import serializers

from apps.accounts.models.user import User
from apps.accounts.services.user_service import soft_delete_user, update_user_profile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "middle_name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "middle_name", "full_name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "email", "is_active", "created_at", "updated_at"]

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, max_length=150)
    last_name = serializers.CharField(required=False, max_length=150)
    middle_name = serializers.CharField(required=False, max_length=150, allow_blank=True)
    email = serializers.EmailField(required=False)

    def update(self, instance, validated_data):
        user = update_user_profile(
            user=instance,
            first_name=validated_data.get("first_name"),
            last_name=validated_data.get("last_name"),
            middle_name=validated_data.get("middle_name"),
            email=validated_data.get("email"),
        )
        return user

