from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import HasObjectPermission, HasPermission
from apps.blog.serializers import PostCreateSerializer, PostSerializer, PostUpdateSerializer

MOCK_POSTS = {
    1: {"id": 1, "title": "Первый пост", "content": "Содержимое первого поста", "author": "admin@test.com", "created_at": "2024-01-01T10:00:00Z"},
    2: {"id": 2, "title": "Второй пост", "content": "Содержимое второго поста", "author": "user@test.com", "created_at": "2024-01-02T11:00:00Z"},
    3: {"id": 3, "title": "Третий пост", "content": "Содержимое третьего поста", "author": "moderator@test.com", "created_at": "2024-01-03T12:00:00Z"},
}


class PostListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, HasPermission]
    resource_type = "blog.post"
    serializer_class = PostSerializer

    def get_required_permission(self, request):
        if request.method == "GET":
            return "blog.post.list"
        elif request.method == "POST":
            return "blog.post.create"
        return None

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PostCreateSerializer
        return PostSerializer

    def list(self, request, *args, **kwargs):
        posts_list = list(MOCK_POSTS.values())
        serializer = self.get_serializer(posts_list, many=True)
        return Response(
            {
                "count": len(MOCK_POSTS),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)


        new_id = max(MOCK_POSTS.keys(), default=0) + 1

        new_post = {
            "id": new_id,
            "title": serializer.validated_data["title"],
            "content": serializer.validated_data["content"],
            "author": request.user.email,
            "created_at": "2024-01-04T13:00:00Z",
        }

        MOCK_POSTS[new_id] = new_post

        response_serializer = PostSerializer(new_post)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class PostDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, HasObjectPermission]
    resource_type = "blog.post"
    serializer_class = PostSerializer
    lookup_field = "post_id"

    def get_required_permission(self, request):
        method = request.method
        if method == "GET":
            return "blog.post.read"
        elif method in ["PUT", "PATCH"]:
            return "blog.post.update"
        elif method == "DELETE":
            return "blog.post.delete"
        return None

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return PostUpdateSerializer
        return PostSerializer

    def get_object(self):
        post_id = self.kwargs.get("post_id")
        if post_id not in MOCK_POSTS:
            from apps.common.exceptions import ResourceNotFoundException

            raise ResourceNotFoundException(
                message="Пост не найден",
                errors=[{"code": "post_not_found", "detail": f"Пост с ID {post_id} не найден"}],
            )

        post = MOCK_POSTS[post_id]
        return type("MockPost", (), {"id": post["id"], "pk": post["id"]})()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        self.check_object_permissions(request, instance)
        post = MOCK_POSTS[instance.id]
        serializer = self.get_serializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        post = MOCK_POSTS[instance.id]
        updated_post = {
            **post,
            **serializer.validated_data,
            "updated_at": "2024-01-04T14:00:00Z",
        }

        MOCK_POSTS[instance.id] = updated_post

        response_serializer = PostSerializer(updated_post)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        del MOCK_POSTS[instance.id]
        return Response(status=status.HTTP_204_NO_CONTENT)

