from datetime import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.models.auth import TokenBlacklist

User = get_user_model()


def generate_tokens(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    
    return {
        "access_token": str(access),
        "refresh_token": str(refresh),
    }


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        access_token = AccessToken(token)
        return access_token.payload
    except Exception:
        return None


def get_token_jti(token: str) -> str | None:
    payload = decode_token(token)
    if payload:
        return payload.get("jti")
    return None


def get_token_expires_at(token: str) -> datetime | None:
    payload = decode_token(token)
    if payload:
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
    return None


def add_token_to_blacklist(token: str, user) -> TokenBlacklist | None:
    jti = get_token_jti(token)
    expires_at = get_token_expires_at(token)
    
    if not jti or not expires_at:
        return None
    
    if TokenBlacklist.is_blacklisted(jti):
        return TokenBlacklist.objects.get(token_jti=jti)
    
    blacklisted_token = TokenBlacklist.objects.create(
        token_jti=jti,
        user=user,
        expires_at=expires_at,
    )
    
    return blacklisted_token


def is_token_blacklisted(token: str) -> bool:
    jti = get_token_jti(token)
    if not jti:
        return False
    
    return TokenBlacklist.is_blacklisted(jti)
