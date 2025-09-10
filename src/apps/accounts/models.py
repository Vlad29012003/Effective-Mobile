from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

User: settings.AUTH_USER_MODEL = get_user_model()


class UserWithHistory(User):
    history = HistoricalRecords(
        excluded_fields=["date_joined", "last_login"],
        m2m_fields=["groups", "user_permissions"],
    )

    def __str__(self) -> str:
        return self.email

    class Meta:
        proxy = True
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-date_joined"]
