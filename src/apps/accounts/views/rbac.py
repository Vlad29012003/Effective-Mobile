from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.schemas import PermissionCheckViewSchema
from apps.accounts.serializers.rbac import PermissionCheckRequestSerializer
from apps.common.permissions import check_permissions


class PermissionCheckView(APIView):

    permission_classes = [IsAuthenticated]

    @PermissionCheckViewSchema.get_schema()
    def post(self, request):
        serializer = PermissionCheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        permission_codes = serializer.validated_data["actions"]

        result = check_permissions(user=request.user, permission_codes=permission_codes)

        return Response(result, status=status.HTTP_200_OK)

