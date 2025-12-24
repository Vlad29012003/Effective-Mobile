from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.accounts.models.rbac import Role
from apps.accounts.models.user import User
from apps.accounts.utils.jwt_utils import add_token_to_blacklist, generate_tokens, is_token_blacklisted
from apps.common.exceptions import BusinessLogicException, ValidationException



def register_user(email: str,password: str,password_confirm: str,first_name: str,last_name: str,middle_name: str = "",) -> tuple[User, dict[str, str]]:
    if password != password_confirm:
        raise ValidationException(
            message="Пароли не совпадают",
            errors=[{"code": "password_mismatch", "detail": "Пароли не совпадают", "attr": "password_confirm"}],
        )

    if User.objects.filter(email=email).exists():
        raise BusinessLogicException(
            message="Пользователь с таким email уже существует",
            errors=[{"code": "email_exists", "detail": "Пользователь с таким email уже существует", "attr": "email"}],
        )

    with transaction.atomic():
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            is_active=True,
        )

        default_role = Role.objects.filter(name="user", is_system=True).first()
        if default_role:
            user.add_role(default_role)

    tokens = generate_tokens(user)

    return user, tokens


def authenticate_user(email: str, password: str) -> tuple[User, dict[str, str]]:
    user = authenticate(username=email, password=password)

    if not user:
        raise ValidationException(
            message="Неверный email или пароль",
            errors=[{"code": "invalid_credentials", "detail": "Неверный email или пароль"}],
        )

    if not user.is_active or user.is_deleted:
        reason = "деактивирован" if not user.is_active else "удален"
        raise ValidationException(
            message=f"Аккаунт {reason}",
            errors=[{"code": "account_inactive", "detail": f"Аккаунт {reason}"}],
        )

    tokens = generate_tokens(user)

    return user, tokens


def logout_user(access_token: str, refresh_token: str, user: User) -> None:
    access_blacklisted = add_token_to_blacklist(access_token, user)
    refresh_blacklisted = add_token_to_blacklist(refresh_token, user)

    if not access_blacklisted and not refresh_blacklisted:
        raise ValidationException(
            message="Не удалось добавить токены в blacklist",
            errors=[{"code": "logout_failed", "detail": "Невалидные токены"}],
        )


def refresh_access_token(refresh_token: str) -> dict[str, str]:
    try:
        refresh = RefreshToken(refresh_token)
    except TokenError:
        raise ValidationException(
            message="Невалидный refresh токен",
            errors=[{"code": "invalid_refresh_token", "detail": "Невалидный refresh токен"}],
        )

    if is_token_blacklisted(refresh_token):
        raise ValidationException(
            message="Refresh токен в blacklist",
            errors=[{"code": "token_blacklisted", "detail": "Refresh токен в blacklist"}],
        )

    user_id = refresh.payload.get("user_id")
    if not user_id:
        raise ValidationException(
            message="Невалидный refresh токен",
            errors=[{"code": "invalid_refresh_token", "detail": "Невалидный refresh токен"}],
        )

    try:
        user = User.objects.get(id=user_id, is_active=True, deleted_at__isnull=True)
    except User.DoesNotExist:
        raise ValidationException(
            message="Пользователь не найден или неактивен",
            errors=[{"code": "user_not_found", "detail": "Пользователь не найден или неактивен"}],
        )

    access_token = refresh.access_token

    return {"access_token": str(access_token)}

