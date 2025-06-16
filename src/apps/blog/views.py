from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from dishka import FromDishka
from drf_spectacular.utils import extend_schema

from config.di.dishka import inject
from .models import Post
from .serializers import PostSerializer
from .services import PostService
from .permissions import IsOwnerOrReadOnly


@extend_schema(tags=['blog'])
class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows posts to be viewed or edited.
    """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['author__username', 'is_published']

    @inject
    def get_queryset(self, service: FromDishka[PostService]):
        """
        This view should return a list of all published posts
        for GET requests, but allow authors to see their unpublished posts.
        """
        if self.action == 'list':
            return PostService.get_published_posts()

        return Post.objects.all().select_related('author')

    @inject
    def perform_create(self, serializer: PostSerializer, service: FromDishka[PostService]):
        """
        Using service to create a post.
        """
        service.create_post(author=self.request.user, data=serializer.validated_data)

    @inject
    def perform_update(self, serializer: PostSerializer, service: FromDishka[PostService]):
        """
        Using service to update a post.
        """
        service.update_post(post=serializer.instance, data=serializer.validated_data)
