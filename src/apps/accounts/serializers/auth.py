from rest_framework import serializers

from apps.accounts.services.auth_service import (
    authenticate_user,
    logout_user,
    refresh_access_token,
    register_user,
)


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    password_confirm = serializers.CharField(required=True, write_only=True, min_length=8)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    middle_name = serializers.CharField(required=False, allow_blank=True, max_length=150, default="")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        user, tokens = register_user(
            email=validated_data["email"],
            password=validated_data["password"],
            password_confirm=validated_data["password_confirm"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            middle_name=validated_data.get("middle_name", ""),
        )
        return {"user": user, "tokens": tokens}


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def create(self, validated_data):
        user, tokens = authenticate_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return {"user": user, "tokens": tokens}


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)

    def create(self, validated_data):
        access_token = refresh_access_token(validated_data["refresh_token"])
        return {"access_token": access_token}


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Пользователь не аутентифицирован")

        access_token = str(request.auth) if request.auth else None
        if not access_token:
            raise serializers.ValidationError("Access токен не найден")

        logout_user(
            access_token=access_token,
            refresh_token=validated_data["refresh_token"],
            user=request.user,
        )
        return {"message": "Выход выполнен успешно"}

