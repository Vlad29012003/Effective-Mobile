from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Post

User: settings.AUTH_USER_MODEL = get_user_model()


class PostService:
    @staticmethod
    def get_published_posts():
        """Returns all published posts with their authors."""
        return Post.published.all().select_related("author")

    @staticmethod
    @transaction.atomic
    def create_post(author: User, data: dict[str, Any]) -> Post:
        post = Post.objects.create(author=author, **data)
        return post

    @staticmethod
    @transaction.atomic
    def update_post(post: Post, data: dict[str, Any]) -> Post:
        for key, value in data.items():
            setattr(post, key, value)

        post.save()
        return post
