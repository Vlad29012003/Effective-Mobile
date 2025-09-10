from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.schemas import PermissionCheckViewSchema
from apps.accounts.serializers import LoginSerializer, PermissionCheckRequestSerializer
from apps.common.permissions import permission_service


@extend_schema(tags=["auth"])
class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data.get("username")
        password = serializer.validated_data.get("password")

        if not username or not password:
            return Response(
                {"detail": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(username=username).first()

        if not user:
            return Response(
                {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if not user.is_active:
            return Response(
                {"detail": "Account is block"}, status=status.HTTP_403_FORBIDDEN
            )

        user = authenticate(request, username=username, password=password)

        if not user:
            return Response(
                {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        login(request, user)
        return Response({"detail": "Login successful"}, status=status.HTTP_200_OK)


class PermissionCheckView(APIView):
    permission_classes = [IsAuthenticated]

    @PermissionCheckViewSchema.get_schema()
    def post(self, request):
        serializer = PermissionCheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actions = serializer.validated_data["actions"]

        result = permission_service.check_permissions(
            user=request.user, actions=actions
        )

        return Response(result, status=status.HTTP_200_OK)
