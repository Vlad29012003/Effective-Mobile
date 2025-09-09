from dishka import FromDishka
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from apps.common.permissions import Permission, has_permission
from config.di.dishka import inject

from .models import Post
from .permissions import IsOwnerOrReadOnly
from .serializers import PostPublishSerializer, PostSerializer
from .services import PostService


@extend_schema(tags=["blog"])
class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows posts to be viewed or edited.
    """

    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["author__username", "is_published"]

    @inject
    def get_queryset(self, service: FromDishka[PostService]):
        """
        Возвращает посты в зависимости от действия и прав пользователя.
        """
        # Проверка для генерации OpenAPI схемы
        if getattr(self, "swagger_fake_view", False):
            return Post.objects.none()

        if self.action == "list":
            # Для списка показываем только опубликованные посты
            return Post.objects.filter(
                id__in=[p.id for p in service.get_published_posts()]
            )
        elif self.action == "my_posts":
            # Для my_posts показываем посты пользователя
            if self.request.user.is_authenticated:
                return Post.objects.filter(
                    id__in=[p.id for p in service.get_user_posts(self.request.user)]
                )
            return Post.objects.none()
        else:
            # Для detail, update, delete - все посты (права проверим в сервисе)
            return Post.objects.all().select_related("author")

    def get_object(self) -> Post:
        """
        Получить объект через сервис с проверкой разрешений.
        """
        obj = super().get_object()

        # Для некоторых действий проверяем через сервис
        if self.action in ["retrieve", "update", "destroy"]:
            service = PostService()
            # Дополнительная проверка через сервис если нужно
            service.get_post_by_id(obj.id, self.request.user)

        return obj

    @inject
    def perform_create(
        self, serializer: PostSerializer, service: FromDishka[PostService]
    ) -> None:
        """
        Создание поста через сервис с проверкой разрешений.
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
        Обновление поста через сервис с проверкой разрешений.
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
        Удаление поста через сервис с проверкой разрешений.
        """
        service.delete_post(instance, self.request.user)

    @extend_schema(
        methods=["GET"],
        summary="Получить мои посты",
        description="Возвращает посты текущего пользователя (включая черновики)",
    )
    @action(
        detail=False, methods=["GET"], permission_classes=[IsAuthenticatedOrReadOnly]
    )
    @inject
    def my_posts(self, request: Request, service: FromDishka[PostService]) -> Response:
        """
        Получить посты текущего пользователя.
        """
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        posts = service.get_user_posts(request.user, include_drafts=True)
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    @extend_schema(
        methods=["POST"],
        summary="Опубликовать пост",
        description="Опубликовать существующий пост",
        request=PostPublishSerializer,
    )
    @action(
        detail=True, methods=["POST"], permission_classes=[IsAuthenticatedOrReadOnly]
    )
    @inject
    def publish(
        self, request: Request, pk: str | None, service: FromDishka[PostService]
    ) -> Response:
        """
        Опубликовать пост.
        """
        post = self.get_object()
        updated_post = service.publish_post(post, request.user)
        serializer = self.get_serializer(updated_post)
        return Response(serializer.data)

    @extend_schema(
        methods=["POST"],
        summary="Снять пост с публикации",
        description="Снять пост с публикации (сделать черновиком)",
    )
    @action(
        detail=True, methods=["POST"], permission_classes=[IsAuthenticatedOrReadOnly]
    )
    @inject
    def unpublish(
        self, request: Request, pk: str | None, *, service: FromDishka[PostService]
    ) -> Response:
        """
        Снять пост с публикации.
        """
        post = self.get_object()
        updated_post = service.unpublish_post(post, request.user)
        serializer = self.get_serializer(updated_post)
        return Response(serializer.data)

    @extend_schema(
        methods=["GET"],
        summary="Проверить разрешения для поста",
        description="Возвращает разрешения текущего пользователя для данного поста",
    )
    @action(
        detail=True, methods=["GET"], permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def permissions(self, request: Request, pk: str | None) -> Response:
        """
        Получить разрешения для поста.
        """
        post = self.get_object()

        if not request.user.is_authenticated:
            permissions_to_check = [Permission.BLOG_VIEW_POST.value]
        else:
            permissions_to_check = [
                Permission.BLOG_VIEW_POST.value,
                Permission.BLOG_EDIT_POST.value,
                Permission.BLOG_DELETE_POST.value,
                Permission.BLOG_PUBLISH_POST.value,
            ]

        result = {}
        for permission in permissions_to_check:
            result[permission] = has_permission(
                request.user, permission, post_author_id=post.author.id
            )

        return Response(result)
