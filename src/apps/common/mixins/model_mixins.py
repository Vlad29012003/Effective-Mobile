from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class HistoryInDefaultDBBase(models.Model):
    """
    An abstract base model that forces its children (history models)
    to be stored in the 'default' database via the router.
    """

    class Meta:
        abstract = True
        _database = "default"


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


class HistoryMixin(models.Model):
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True


class TimestampHistoryMixin(TimestampMixin):
    """
    Mixin that combines TimestampMixin and HistoryMixin.
    It provides both created_at/updated_at fields and historical records.
    """

    history = HistoricalRecords(
        inherit=True,
        excluded_fields=["created_at", "updated_at"],
        bases=[HistoryInDefaultDBBase],
    )

    class Meta:
        abstract = True
