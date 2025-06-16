from typing import Dict, Any
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Post

User = get_user_model()

class PostService:
    @staticmethod
    def get_published_posts():
        """Returns all published posts with their authors."""
        return Post.published.all().select_related('author')

    @staticmethod
    @transaction.atomic
    def create_post(author: User, data: Dict[str, Any]) -> Post:
        post = Post.objects.create(author=author, **data)
        return post

    @staticmethod
    @transaction.atomic
    def update_post(post: Post, data: Dict[str, Any]) -> Post:
        for key, value in data.items():
            setattr(post, key, value)

        post.save()
        return post