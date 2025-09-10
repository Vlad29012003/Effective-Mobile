from dishka import FromDishka
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from config.di.dishka import inject

from .models import Post
from .permissions import IsOwnerOrReadOnly
from .schemas import PostPublishActionSchema, PostUnpublishActionSchema
from .serializers import PostSerializer
from .services import PostService


@extend_schema(tags=["blog"])
class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows posts to be viewed or edited.
    """

    queryset = Post.objects.none()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["author__username", "is_published"]

    def get_queryset(self):
        """
        Returns posts based on action and user permissions.
        Optimized method without duplicate database queries.
        """
        if self.action == "list":
            return Post.objects.filter(is_published=True).select_related("author")
        if self.action == "my_posts":
            return Post.objects.filter(author=self.request.user).select_related(
                "author"
            )

        return Post.objects.all().select_related("author")

    @inject
    def get_object(self, service: FromDishka[PostService]) -> Post:
        """
        Get object through service with permission checking.
        """
        obj = super().get_object()

        if self.action in ["retrieve", "update", "destroy"]:
            service.get_post_by_id(obj.id, self.request.user)

        return obj

    @inject
    def perform_create(
        self, serializer: PostSerializer, service: FromDishka[PostService]
    ) -> None:
        """
        Create post through service with permission checking.
        """
        post = service.create_post(
            author=self.request.user, data=serializer.validated_data
        )
        serializer.instance = post

    @inject
    def perform_update(
        self, serializer: PostSerializer, service: FromDishka[PostService]
    ) -> None:
        """
        Update post through service with permission checking.
        """
        post = service.update_post(
            post=serializer.instance,
            data=serializer.validated_data,
            user=self.request.user,
        )
        serializer.instance = post

    @inject
    def perform_destroy(self, instance: Post, service: FromDishka[PostService]) -> None:
        """
        Delete post through service with permission checking.
        """
        service.delete_post(instance, self.request.user)

    @action(
        detail=False, methods=["GET"], permission_classes=[IsAuthenticatedOrReadOnly]
    )
    @inject
    def my_posts(self, request: Request, service: FromDishka[PostService]) -> Response:
        """
        List posts of the authenticated user.
        """
        posts = service.get_user_posts(request.user, include_drafts=True)
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    @PostPublishActionSchema.get_schema()
    @action(
        detail=True, methods=["POST"], permission_classes=[IsAuthenticatedOrReadOnly]
    )
    @inject
    def publish(
        self, request: Request, pk: str | None, service: FromDishka[PostService]
    ) -> Response:
        """
        Publish a post.
        """
        post = self.get_object()
        updated_post = service.publish_post(post, request.user)
        serializer = self.get_serializer(updated_post)
        return Response(serializer.data)

    @PostUnpublishActionSchema.get_schema()
    @action(
        detail=True, methods=["POST"], permission_classes=[IsAuthenticatedOrReadOnly]
    )
    @inject
    def unpublish(
        self, request: Request, pk: str | None, *, service: FromDishka[PostService]
    ) -> Response:
        """
        Unpublish a post.
        """
        post = self.get_object()
        updated_post = service.unpublish_post(post, request.user)
        serializer = self.get_serializer(updated_post)
        return Response(serializer.data)
