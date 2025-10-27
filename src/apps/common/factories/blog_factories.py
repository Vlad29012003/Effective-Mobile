import factory
from factory.django import DjangoModelFactory

from apps.blog.models import Post, PostImage

from .user_factories import UserFactory


class PostFactory(DjangoModelFactory):
    class Meta:
        model = Post

    author = factory.SubFactory(UserFactory)
    title = factory.Faker("sentence")
    content = factory.Faker("paragraph")
    is_published = factory.Faker("boolean")


class PostImageFactory(DjangoModelFactory):
    class Meta:
        model = PostImage

    post = factory.SubFactory(PostFactory)
    image = factory.django.ImageField(color="yellow")
    caption = factory.Faker("paragraph")
