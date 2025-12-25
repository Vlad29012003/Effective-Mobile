from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers.user import UserProfileSerializer, UserUpdateSerializer
from apps.accounts.services.user_service import soft_delete_user


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UserUpdateSerializer(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        response_serializer = UserProfileSerializer(updated_user)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserUpdateSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        response_serializer = UserProfileSerializer(updated_user)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        soft_delete_user(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

