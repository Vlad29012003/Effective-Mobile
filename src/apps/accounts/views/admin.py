from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models.rbac import Permission, Role, RolePermission, UserRole
from apps.accounts.models.user import User
from apps.accounts.permissions.admin import IsAdmin
from apps.accounts.serializers.admin import (
    AdminUserSerializer,
    PermissionCreateSerializer,
    PermissionSerializer,
    RoleCreateSerializer,
    RolePermissionAssignSerializer,
    RolePermissionSerializer,
    RoleSerializer,
    UserRoleAssignSerializer,
    UserRoleSerializer,
)
from apps.common.exceptions import BusinessLogicException, ResourceNotFoundException


class RoleListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        roles = Role.objects.all().order_by("name")
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RoleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        response_serializer = RoleSerializer(role)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, role_id):
        try:
            return Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise ResourceNotFoundException(
                message="Роль не найдена",
                errors=[{"code": "role_not_found", "detail": f"Роль с ID {role_id} не найдена"}],
            )

    def get(self, request, role_id):
        role = self.get_object(role_id)
        serializer = RoleSerializer(role)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, role_id):
        role = self.get_object(role_id)
        serializer = RoleCreateSerializer(role, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_role = serializer.save()
        response_serializer = RoleSerializer(updated_role)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, role_id):
        role = self.get_object(role_id)
        serializer = RoleCreateSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_role = serializer.save()
        response_serializer = RoleSerializer(updated_role)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, role_id):
        role = self.get_object(role_id)
        if role.is_system:
            raise BusinessLogicException(
                message="Системные роли нельзя удалять",
                errors=[{"code": "system_role", "detail": "Системные роли нельзя удалять"}],
            )
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PermissionListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        permissions = Permission.objects.all().order_by("code")
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PermissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permission = serializer.save()
        response_serializer = PermissionSerializer(permission)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class PermissionDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, permission_id):
        try:
            return Permission.objects.get(id=permission_id)
        except Permission.DoesNotExist:
            raise ResourceNotFoundException(
                message="Право не найдено",
                errors=[{"code": "permission_not_found", "detail": f"Право с ID {permission_id} не найдено"}],
            )

    def get(self, request, permission_id):
        permission = self.get_object(permission_id)
        serializer = PermissionSerializer(permission)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, permission_id):
        permission = self.get_object(permission_id)
        serializer = PermissionCreateSerializer(permission, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_permission = serializer.save()
        response_serializer = PermissionSerializer(updated_permission)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, permission_id):
        permission = self.get_object(permission_id)
        serializer = PermissionCreateSerializer(permission, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_permission = serializer.save()
        response_serializer = PermissionSerializer(updated_permission)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, permission_id):
        permission = self.get_object(permission_id)
        permission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RolePermissionListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_role(self, role_id):
        try:
            return Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise ResourceNotFoundException(
                message="Роль не найдена",
                errors=[{"code": "role_not_found", "detail": f"Роль с ID {role_id} не найдена"}],
            )

    def get(self, request, role_id):
        role = self.get_role(role_id)
        role_permissions = RolePermission.objects.filter(role=role).select_related("permission")
        serializer = RolePermissionSerializer(role_permissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, role_id):
        role = self.get_role(role_id)
        serializer = RolePermissionAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        permission_id = serializer.validated_data["permission_id"]
        try:
            permission = Permission.objects.get(id=permission_id)
        except Permission.DoesNotExist:
            raise ResourceNotFoundException(
                message="Право не найдено",
                errors=[{"code": "permission_not_found", "detail": f"Право с ID {permission_id} не найдено"}],
            )

        role_permission, created = RolePermission.objects.get_or_create(role=role, permission=permission)
        response_serializer = RolePermissionSerializer(role_permission)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class RolePermissionDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_role(self, role_id):
        try:
            return Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise ResourceNotFoundException(
                message="Роль не найдена",
                errors=[{"code": "role_not_found", "detail": f"Роль с ID {role_id} не найдена"}],
            )

    def delete(self, request, role_id, permission_id):
        role = self.get_role(role_id)
        try:
            permission = Permission.objects.get(id=permission_id)
        except Permission.DoesNotExist:
            raise ResourceNotFoundException(
                message="Право не найдено",
                errors=[{"code": "permission_not_found", "detail": f"Право с ID {permission_id} не найдено"}],
            )

        role_permission = RolePermission.objects.filter(role=role, permission=permission).first()
        if not role_permission:
            raise ResourceNotFoundException(
                message="Связь роль-право не найдена",
                errors=[{"code": "role_permission_not_found", "detail": "Связь роль-право не найдена"}],
            )

        role_permission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        users = User.objects.filter(is_active=True, deleted_at__isnull=True).order_by("email")
        serializer = AdminUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRoleListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id, is_active=True, deleted_at__isnull=True)
        except User.DoesNotExist:
            raise ResourceNotFoundException(
                message="Пользователь не найден",
                errors=[{"code": "user_not_found", "detail": f"Пользователь с ID {user_id} не найден"}],
            )

    def get(self, request, user_id):
        user = self.get_user(user_id)
        user_roles = UserRole.objects.filter(user=user).select_related("role")
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, user_id):
        user = self.get_user(user_id)
        serializer = UserRoleAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role_id = serializer.validated_data["role_id"]
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise ResourceNotFoundException(
                message="Роль не найдена",
                errors=[{"code": "role_not_found", "detail": f"Роль с ID {role_id} не найдена"}],
            )

        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=role,
            defaults={"assigned_by": request.user},
        )
        response_serializer = UserRoleSerializer(user_role)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class UserRoleDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id, is_active=True, deleted_at__isnull=True)
        except User.DoesNotExist:
            raise ResourceNotFoundException(
                message="Пользователь не найден",
                errors=[{"code": "user_not_found", "detail": f"Пользователь с ID {user_id} не найден"}],
            )

    def delete(self, request, user_id, role_id):
        user = self.get_user(user_id)
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise ResourceNotFoundException(
                message="Роль не найдена",
                errors=[{"code": "role_not_found", "detail": f"Роль с ID {role_id} не найдена"}],
            )

        user.remove_role(role)
        return Response(status=status.HTTP_204_NO_CONTENT)

