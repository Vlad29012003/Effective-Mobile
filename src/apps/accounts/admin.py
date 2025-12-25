from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.models.auth import TokenBlacklist
from apps.accounts.models.object_permission import RoleObjectPermission, UserObjectPermission
from apps.accounts.models.rbac import Permission, Role, RolePermission, UserRole
from apps.accounts.models.user import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "first_name", "last_name", "is_active", "is_staff", "is_superuser", "deleted_at", "date_joined"]
    list_filter = ["is_active", "is_staff", "is_superuser", "deleted_at", "date_joined"]
    search_fields = ["email", "first_name", "last_name", "middle_name"]
    ordering = ["email"]
    readonly_fields = ["date_joined", "last_login", "deleted_at"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "middle_name")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "deleted_at")}),
    )

    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "first_name", "last_name")}),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:
            readonly.append("email")
        return readonly


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1
    autocomplete_fields = ["permission"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "is_system", "created_at", "updated_at"]
    list_filter = ["is_system", "created_at", "updated_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [RolePermissionInline]

    fieldsets = (
        (None, {"fields": ("name", "description", "is_system")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "resource_type", "action", "created_at"]
    list_filter = ["resource_type", "action", "created_at"]
    search_fields = ["code", "name", "description", "resource_type"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("code", "name", "description")}),
        (_("Resource"), {"fields": ("resource_type", "action")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ["role", "permission", "created_at"]
    list_filter = ["role", "permission", "created_at"]
    search_fields = ["role__name", "permission__code", "permission__name"]
    autocomplete_fields = ["role", "permission"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "assigned_by", "assigned_at"]
    list_filter = ["role", "assigned_at"]
    search_fields = ["user__email", "role__name", "assigned_by__email"]
    autocomplete_fields = ["user", "role", "assigned_by"]
    readonly_fields = ["assigned_at", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("user", "role", "assigned_by")}),
        (_("Timestamps"), {"fields": ("assigned_at", "created_at", "updated_at")}),
    )


@admin.register(UserObjectPermission)
class UserObjectPermissionAdmin(admin.ModelAdmin):
    list_display = ["user", "permission", "resource_type", "resource_id", "is_granted", "granted_by", "granted_at"]
    list_filter = ["is_granted", "resource_type", "permission", "granted_at"]
    search_fields = ["user__email", "permission__code", "resource_type", "resource_id"]
    autocomplete_fields = ["user", "permission", "granted_by"]
    readonly_fields = ["granted_at", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("user", "permission")}),
        (_("Resource"), {"fields": ("resource_type", "resource_id", "is_granted")}),
        (_("Grant info"), {"fields": ("granted_by", "granted_at")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(RoleObjectPermission)
class RoleObjectPermissionAdmin(admin.ModelAdmin):
    list_display = ["role", "permission", "resource_type", "resource_id", "is_granted", "granted_by", "granted_at"]
    list_filter = ["is_granted", "resource_type", "permission", "role", "granted_at"]
    search_fields = ["role__name", "permission__code", "resource_type", "resource_id"]
    autocomplete_fields = ["role", "permission", "granted_by"]
    readonly_fields = ["granted_at", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("role", "permission")}),
        (_("Resource"), {"fields": ("resource_type", "resource_id", "is_granted")}),
        (_("Grant info"), {"fields": ("granted_by", "granted_at")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(TokenBlacklist)
class TokenBlacklistAdmin(admin.ModelAdmin):
    list_display = ["user", "token_jti", "expires_at", "blacklisted_at"]
    list_filter = ["blacklisted_at", "expires_at"]
    search_fields = ["user__email", "token_jti"]
    readonly_fields = ["blacklisted_at", "created_at", "updated_at"]
    autocomplete_fields = ["user"]

    fieldsets = (
        (None, {"fields": ("user", "token_jti")}),
        (_("Dates"), {"fields": ("expires_at", "blacklisted_at")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )

