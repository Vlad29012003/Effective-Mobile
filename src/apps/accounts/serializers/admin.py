from rest_framework import serializers

from apps.accounts.models.rbac import Permission, PermissionAction, Role, RolePermission, UserRole
from apps.accounts.models.user import User


class RoleSerializer(serializers.ModelSerializer):
    permissions_count = serializers.SerializerMethodField()
    can_be_deleted = serializers.BooleanField(read_only=True)

    class Meta:
        model = Role
        fields = ["id", "name", "description", "is_system", "permissions_count", "can_be_deleted", "created_at", "updated_at"]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]

    def get_permissions_count(self, obj):
        return obj.get_permissions().count()


class RoleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["name", "description"]
        extra_kwargs = {
            "name": {"required": True},
            "description": {"required": False, "allow_blank": True},
        }

    def validate_name(self, value):
        if Role.objects.filter(name=value).exists():
            raise serializers.ValidationError("Роль с таким именем уже существует")
        return value


class PermissionSerializer(serializers.ModelSerializer):
    action_display = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ["id", "code", "name", "description", "resource_type", "action", "action_display", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_action_display(self, obj):
        return dict(PermissionAction.choices).get(obj.action, obj.action)


class PermissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["code", "name", "description", "resource_type", "action"]
        extra_kwargs = {
            "code": {"required": True},
            "name": {"required": True},
            "resource_type": {"required": True},
            "action": {"required": True},
            "description": {"required": False, "allow_blank": True},
        }

    def validate_code(self, value):
        if Permission.objects.filter(code=value).exists():
            raise serializers.ValidationError("Право с таким кодом уже существует")
        return value

    def validate_action(self, value):
        valid_actions = [choice[0] for choice in PermissionAction.choices]
        if value not in valid_actions:
            raise serializers.ValidationError(f"Действие должно быть одним из: {', '.join(valid_actions)}")
        return value


class RolePermissionSerializer(serializers.ModelSerializer):
    permission_code = serializers.CharField(source="permission.code", read_only=True)
    permission_name = serializers.CharField(source="permission.name", read_only=True)

    class Meta:
        model = RolePermission
        fields = ["id", "role", "permission", "permission_code", "permission_name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RolePermissionAssignSerializer(serializers.Serializer):
    permission_id = serializers.IntegerField(required=True)

    def validate_permission_id(self, value):
        if not Permission.objects.filter(id=value).exists():
            raise serializers.ValidationError("Право с таким ID не существует")
        return value


class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    role_description = serializers.CharField(source="role.description", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = UserRole
        fields = ["id", "user", "role", "role_name", "role_description", "user_email", "assigned_by", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserRoleAssignSerializer(serializers.Serializer):
    role_id = serializers.IntegerField(required=True)

    def validate_role_id(self, value):
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Роль с таким ID не существует")
        return value


class AdminUserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "middle_name", "is_active", "roles", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_roles(self, obj):
        return [role.name for role in obj.get_roles()]

