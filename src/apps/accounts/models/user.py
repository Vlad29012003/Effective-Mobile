from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.mixins.model_mixins import TimestampMixin


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен для создания пользователя")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, TimestampMixin):

    username = None
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    middle_name = models.CharField(_("middle name"), max_length=150, blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    deleted_at = models.DateTimeField(_("deleted at"), null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        db_table = "users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(filter(None, parts)).strip() or self.email

    def soft_delete(self):
        self.is_active = False
        from django.utils import timezone

        self.deleted_at = timezone.now()
        self.save(update_fields=["is_active", "deleted_at"])

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def get_roles(self):
        from apps.accounts.models.rbac import Role

        return Role.objects.filter(user_roles__user=self).distinct()

    def has_role(self, role_name):
        return self.user_roles.filter(role__name=role_name).exists()

    def add_role(self, role, assigned_by=None):
        from apps.accounts.models.rbac import UserRole

        UserRole.objects.get_or_create(
            user=self,
            role=role,
            defaults={"assigned_by": assigned_by},
        )

    def remove_role(self, role):
        self.user_roles.filter(role=role).delete()

