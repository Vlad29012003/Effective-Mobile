from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from apps.accounts.utils.jwt_utils import is_token_blacklisted


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        if is_token_blacklisted(str(raw_token)):
            raise InvalidToken("Token is blacklisted")

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
        except TokenError:
            raise InvalidToken("Token is invalid or expired")

        return (user, validated_token)
