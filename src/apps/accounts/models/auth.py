from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.mixins.model_mixins import TimestampMixin


class TokenBlacklist(TimestampMixin):
    token_jti = models.CharField(_("token jti"), max_length=255, unique=True, db_index=True)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="blacklisted_tokens", verbose_name=_("user"))
    expires_at = models.DateTimeField(_("expires at"))
    blacklisted_at = models.DateTimeField(_("blacklisted at"), auto_now_add=True)

    class Meta:
        verbose_name = _("token blacklist")
        verbose_name_plural = _("token blacklist")
        db_table = "token_blacklist"
        indexes = [
            models.Index(fields=["token_jti"]),
            models.Index(fields=["user"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Blacklisted token {self.token_jti} for {self.user.email}"

    @classmethod
    def cleanup_expired(cls):
        from django.utils import timezone

        return cls.objects.filter(expires_at__lt=timezone.now()).delete()

    @classmethod
    def is_blacklisted(cls, token_jti):
        return cls.objects.filter(token_jti=token_jti).exists()

