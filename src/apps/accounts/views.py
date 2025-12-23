from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.schemas import PermissionCheckViewSchema
from apps.accounts.serializers import PermissionCheckRequestSerializer
from apps.common.permissions import permission_service


class PermissionCheckView(APIView):
    permission_classes = [IsAuthenticated]

    @PermissionCheckViewSchema.get_schema()
    def post(self, request):
        serializer = PermissionCheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actions = serializer.validated_data["actions"]

        result = permission_service.check_permissions(user=request.user, actions=actions)

        return Response(result, status=status.HTTP_200_OK)
