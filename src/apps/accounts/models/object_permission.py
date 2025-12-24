from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.mixins.model_mixins import TimestampMixin


class UserObjectPermission(TimestampMixin):

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="user_object_permissions", verbose_name=_("user"))
    permission = models.ForeignKey("accounts.Permission", on_delete=models.CASCADE, related_name="user_object_permissions", verbose_name=_("permission"))
    resource_type = models.CharField(_("resource type"), max_length=100)
    resource_id = models.PositiveIntegerField(_("resource id"))
    is_granted = models.BooleanField(_("is granted"), default=True)
    granted_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="granted_user_object_permissions", verbose_name=_("granted by"))
    granted_at = models.DateTimeField(_("granted at"), auto_now_add=True)

    class Meta:
        verbose_name = _("user object permission")
        verbose_name_plural = _("user object permissions")
        db_table = "user_object_permissions"
        unique_together = [["user", "permission", "resource_type", "resource_id"]]
        indexes = [
            models.Index(fields=["user", "resource_type", "resource_id"]),
            models.Index(fields=["user", "is_granted"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["granted_at"]),
        ]

    def __str__(self):
        action = "grant" if self.is_granted else "deny"
        return f"{self.user.email} -> {action} {self.permission.code} on {self.resource_type}#{self.resource_id}"


class RoleObjectPermission(TimestampMixin):

    role = models.ForeignKey("accounts.Role", on_delete=models.CASCADE, related_name="role_object_permissions", verbose_name=_("role"))
    permission = models.ForeignKey("accounts.Permission", on_delete=models.CASCADE, related_name="role_object_permissions", verbose_name=_("permission"))
    resource_type = models.CharField(_("resource type"), max_length=100)
    resource_id = models.PositiveIntegerField(_("resource id"))
    is_granted = models.BooleanField(_("is granted"), default=True)
    granted_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="granted_role_object_permissions", verbose_name=_("granted by"))
    granted_at = models.DateTimeField(_("granted at"), auto_now_add=True)

    class Meta:
        verbose_name = _("role object permission")
        verbose_name_plural = _("role object permissions")
        db_table = "role_object_permissions"
        unique_together = [["role", "permission", "resource_type", "resource_id"]]
        indexes = [
            models.Index(fields=["role", "resource_type", "resource_id"]),
            models.Index(fields=["role", "is_granted"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["granted_at"]),
        ]

    def __str__(self):
        action = "grant" if self.is_granted else "deny"
        return f"{self.role.name} -> {action} {self.permission.code} on {self.resource_type}#{self.resource_id}"

