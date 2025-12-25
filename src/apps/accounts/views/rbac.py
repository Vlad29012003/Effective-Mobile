from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.serializers.rbac import PermissionCheckRequestSerializer
from apps.common.permissions import check_permissions


class PermissionCheckView(CreateAPIView):
    serializer_class = PermissionCheckRequestSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        permission_codes = serializer.validated_data["actions"]
        result = check_permissions(user=request.user, permission_codes=permission_codes)

        return Response(result, status=status.HTTP_200_OK)

