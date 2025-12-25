from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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


class RoleListView(ListCreateAPIView):
    queryset = Role.objects.all().order_by("name")
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RoleCreateSerializer
        return RoleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        response_serializer = RoleSerializer(role)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class RoleDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    lookup_field = "role_id"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return RoleCreateSerializer
        return RoleSerializer

    def get_object(self):
        try:
            return self.get_queryset().get(id=self.kwargs["role_id"])
        except Role.DoesNotExist:
            raise ResourceNotFoundException(
                message="Роль не найдена",
                errors=[{"code": "role_not_found", "detail": f"Роль с ID {self.kwargs['role_id']} не найдена"}],
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_role = serializer.save()
        response_serializer = RoleSerializer(updated_role)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_system:
            raise BusinessLogicException(
                message="Системные роли нельзя удалять",
                errors=[{"code": "system_role", "detail": "Системные роли нельзя удалять"}],
            )
        return super().destroy(request, *args, **kwargs)


class PermissionListView(ListCreateAPIView):
    queryset = Permission.objects.all().order_by("code")
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PermissionCreateSerializer
        return PermissionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permission = serializer.save()
        response_serializer = PermissionSerializer(permission)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class PermissionDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    lookup_field = "permission_id"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return PermissionCreateSerializer
        return PermissionSerializer

    def get_object(self):
        try:
            return self.get_queryset().get(id=self.kwargs["permission_id"])
        except Permission.DoesNotExist:
            raise ResourceNotFoundException(
                message="Право не найдено",
                errors=[{"code": "permission_not_found", "detail": f"Право с ID {self.kwargs['permission_id']} не найдено"}],
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_permission = serializer.save()
        response_serializer = PermissionSerializer(updated_permission)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class RolePermissionListView(ListCreateAPIView):
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        role_id = self.kwargs["role_id"]
        role = self.get_role(role_id)
        return RolePermission.objects.filter(role=role).select_related("permission")

    def get_role(self, role_id):
        try:
            return Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise ResourceNotFoundException(
                message="Роль не найдена",
                errors=[{"code": "role_not_found", "detail": f"Роль с ID {role_id} не найдена"}],
            )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RolePermissionAssignSerializer
        return RolePermissionSerializer

    def create(self, request, *args, **kwargs):
        role = self.get_role(kwargs["role_id"])
        serializer = self.get_serializer(data=request.data)
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


class RolePermissionDetailView(DestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_role(self, role_id):
        try:
            return Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise ResourceNotFoundException(
                message="Роль не найдена",
                errors=[{"code": "role_not_found", "detail": f"Роль с ID {role_id} не найдена"}],
            )

    def get_object(self):
        role_id = self.kwargs["role_id"]
        permission_id = self.kwargs["permission_id"]
        
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
                message="Связь роли и права не найдена",
                errors=[{"code": "role_permission_not_found", "detail": "Связь роли и права не найдена"}],
            )

        return role_permission


class UserListView(ListAPIView):
    queryset = User.objects.filter(is_active=True, deleted_at__isnull=True).order_by("email")
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class UserRoleListView(ListCreateAPIView):
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        user = self.get_user(user_id)
        return UserRole.objects.filter(user=user).select_related("role")

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id, is_active=True, deleted_at__isnull=True)
        except User.DoesNotExist:
            raise ResourceNotFoundException(
                message="Пользователь не найден",
                errors=[{"code": "user_not_found", "detail": f"Пользователь с ID {user_id} не найден"}],
            )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserRoleAssignSerializer
        return UserRoleSerializer

    def create(self, request, *args, **kwargs):
        user = self.get_user(kwargs["user_id"])
        serializer = self.get_serializer(data=request.data)
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


class UserRoleDetailView(DestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id, is_active=True, deleted_at__isnull=True)
        except User.DoesNotExist:
            raise ResourceNotFoundException(
                message="Пользователь не найден",
                errors=[{"code": "user_not_found", "detail": f"Пользователь с ID {user_id} не найден"}],
            )

    def get_object(self):
        user_id = self.kwargs["user_id"]
        role_id = self.kwargs["role_id"]
        
        user = self.get_user(user_id)
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise ResourceNotFoundException(
                message="Роль не найдена",
                errors=[{"code": "role_not_found", "detail": f"Роль с ID {role_id} не найдена"}],
            )

        user_role = UserRole.objects.filter(user=user, role=role).first()
        if not user_role:
            raise ResourceNotFoundException(
                message="Роль не назначена пользователю",
                errors=[{"code": "user_role_not_found", "detail": "Роль не назначена пользователю"}],
            )

        return user_role

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.user.remove_role(instance.role)
        return Response(status=status.HTTP_204_NO_CONTENT)

