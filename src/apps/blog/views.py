from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasObjectPermission, HasPermission


class PostListView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    resource_type = "blog.post"

    MOCK_POSTS = [
        {"id": 1, "title": "Первый пост", "content": "Содержимое первого поста", "author": "admin@test.com", "created_at": "2024-01-01T10:00:00Z"},
        {"id": 2, "title": "Второй пост", "content": "Содержимое второго поста", "author": "user@test.com", "created_at": "2024-01-02T11:00:00Z"},
        {"id": 3, "title": "Третий пост", "content": "Содержимое третьего поста", "author": "moderator@test.com", "created_at": "2024-01-03T12:00:00Z"},
    ]

    def get(self, request):
        return Response(
            {
                "count": len(self.MOCK_POSTS),
                "results": self.MOCK_POSTS,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        data = request.data
        new_post = {
            "id": len(self.MOCK_POSTS) + 1,
            "title": data.get("title", "Новый пост"),
            "content": data.get("content", ""),
            "author": request.user.email,
            "created_at": "2024-01-04T13:00:00Z",
        }

        return Response(new_post, status=status.HTTP_201_CREATED)


class PostDetailView(APIView):
    permission_classes = [IsAuthenticated, HasObjectPermission]
    resource_type = "blog.post"

    MOCK_POSTS = {
        1: {"id": 1, "title": "Первый пост", "content": "Содержимое первого поста", "author": "admin@test.com", "created_at": "2024-01-01T10:00:00Z"},
        2: {"id": 2, "title": "Второй пост", "content": "Содержимое второго поста", "author": "user@test.com", "created_at": "2024-01-02T11:00:00Z"},
        3: {"id": 3, "title": "Третий пост", "content": "Содержимое третьего поста", "author": "moderator@test.com", "created_at": "2024-01-03T12:00:00Z"},
    }

    def get_required_permission(self, request):
        method = request.method
        if method == "GET":
            return "blog.post.read"
        elif method in ["PUT", "PATCH"]:
            return "blog.post.update"
        elif method == "DELETE":
            return "blog.post.delete"
        return None

    def get_object(self):
        post_id = self.kwargs.get("post_id")
        if post_id not in self.MOCK_POSTS:
            from apps.common.exceptions import ResourceNotFoundException

            raise ResourceNotFoundException(
                message="Пост не найден",
                errors=[{"code": "post_not_found", "detail": f"Пост с ID {post_id} не найден"}],
            )

        post = self.MOCK_POSTS[post_id]
        return type("MockPost", (), {"id": post["id"], "pk": post["id"]})()

    def get(self, request, post_id):
        self.kwargs["post_id"] = post_id
        obj = self.get_object()
        post = self.MOCK_POSTS.get(obj.id)
        return Response(post, status=status.HTTP_200_OK)

    def put(self, request, post_id):
        self.kwargs["post_id"] = post_id
        obj = self.get_object()
        post = self.MOCK_POSTS[obj.id]

        updated_post = {
            **post,
            "title": request.data.get("title", post["title"]),
            "content": request.data.get("content", post["content"]),
            "updated_at": "2024-01-04T14:00:00Z",
        }

        return Response(updated_post, status=status.HTTP_200_OK)

    def patch(self, request, post_id):
        self.kwargs["post_id"] = post_id
        obj = self.get_object()
        post = self.MOCK_POSTS[obj.id]

        updated_post = {
            **post,
            **{k: v for k, v in request.data.items() if k in ["title", "content"]},
            "updated_at": "2024-01-04T14:00:00Z",
        }

        return Response(updated_post, status=status.HTTP_200_OK)

    def delete(self, request, post_id):
        self.kwargs["post_id"] = post_id
        obj = self.get_object()
        return Response(status=status.HTTP_204_NO_CONTENT)

