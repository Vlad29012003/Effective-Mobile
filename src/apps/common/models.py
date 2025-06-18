from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampMixin(models.Model):
    created_at = models.DateTimeField(
        verbose_name=_("Created at"),
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name=_("Updated at"),
        auto_now=True,
    )

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(
        verbose_name=_("UUID"),
        primary_key=True,
        default=uuid4,
        editable=False,
    )

    class Meta:
        abstract = True
