from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.mixins.model_mixins import TimestampMixin


class PermissionAction(models.TextChoices):

    CREATE = "create", _("Create")
    READ = "read", _("Read")
    UPDATE = "update", _("Update")
    DELETE = "delete", _("Delete")
    LIST = "list", _("List")


class Role(TimestampMixin):

    name = models.CharField(_("name"), max_length=100, unique=True)
    description = models.TextField(_("description"), blank=True)
    is_system = models.BooleanField(_("system role"), default=False)

    class Meta:
        verbose_name = _("role")
        verbose_name_plural = _("roles")
        db_table = "roles"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_system"]),
        ]

    def __str__(self):
        return self.name

    @property
    def can_be_deleted(self):
        return not self.is_system

    def get_permissions(self):
        return Permission.objects.filter(role_permissions__role=self).distinct()

    def add_permission(self, permission):
        RolePermission.objects.get_or_create(role=self, permission=permission)

    def remove_permission(self, permission):
        self.role_permissions.filter(permission=permission).delete()


class Permission(TimestampMixin):

    code = models.CharField(_("code"), max_length=200, unique=True)
    name = models.CharField(_("name"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    resource_type = models.CharField(_("resource type"), max_length=100)
    action = models.CharField(_("action"), max_length=50, choices=PermissionAction.choices)

    class Meta:
        verbose_name = _("permission")
        verbose_name_plural = _("permissions")
        db_table = "permissions"
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["resource_type"]),
            models.Index(fields=["action"]),
            models.Index(fields=["resource_type", "action"]),
        ]

    def __str__(self):
        return f"{self.code} ({self.name})"


class RolePermission(TimestampMixin):

    role = models.ForeignKey("accounts.Role", on_delete=models.CASCADE, related_name="role_permissions", verbose_name=_("role"))
    permission = models.ForeignKey("accounts.Permission", on_delete=models.CASCADE, related_name="role_permissions", verbose_name=_("permission"))

    class Meta:
        verbose_name = _("role permission")
        verbose_name_plural = _("role permissions")
        db_table = "role_permissions"
        unique_together = [["role", "permission"]]
        indexes = [
            models.Index(fields=["role", "permission"]),
        ]

    def __str__(self):
        return f"{self.role.name} -> {self.permission.code}"


class UserRole(TimestampMixin):

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="user_roles", verbose_name=_("user"))
    role = models.ForeignKey("accounts.Role", on_delete=models.CASCADE, related_name="user_roles", verbose_name=_("role"))
    assigned_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_roles", verbose_name=_("assigned by"))
    assigned_at = models.DateTimeField(_("assigned at"), auto_now_add=True)

    class Meta:
        verbose_name = _("user role")
        verbose_name_plural = _("user roles")
        db_table = "user_roles"
        unique_together = [["user", "role"]]
        indexes = [
            models.Index(fields=["user", "role"]),
            models.Index(fields=["assigned_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.role.name}"

