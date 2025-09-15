import logging
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.constants import AppPrefixes
from apps.common.exceptions import (
    BusinessLogicException,
    PermissionDeniedException,
    ResourceNotFoundException,
    ValidationException,
)
from apps.common.permissions import has_permission

from .models import Post
from .permissions import BlogPermission

User: settings.AUTH_USER_MODEL = get_user_model()
logger = logging.getLogger(__name__)


class PostService:
    @staticmethod
    def get_published_posts() -> list[Post]:
        logger.info(
            "Fetching published posts",
            extra={"action": "get_published_posts", "service": "PostService"},
        )

        return list(Post.published.all().select_related("author"))

    @staticmethod
    def get_user_posts(user: User, include_drafts: bool = True) -> list[Post]:
        logger.info(
            "Fetching user posts",
            extra={
                "action": "get_user_posts",
                "user_id": user.id,
                "include_drafts": include_drafts,
                "service": "PostService",
            },
        )

        queryset = Post.objects.filter(author=user).select_related("author")

        if not include_drafts:
            queryset = queryset.filter(is_published=True)

        return list(queryset)

    @staticmethod
    def get_post_by_id(post_id: int, user: User = None) -> Post:
        try:
            post = Post.objects.select_related("author").get(id=post_id)
        except Post.DoesNotExist:
            logger.warning(
                "Post not found",
                extra={
                    "action": "get_post_by_id",
                    "post_id": post_id,
                    "service": "PostService",
                },
            )
            raise ResourceNotFoundException(_("Post not found"))

        # Check view permissions
        if not post.is_published and user:
            if not has_permission(
                user, f"{AppPrefixes.BLOG}.{BlogPermission.VIEW_POST.value}"
            ):
                logger.warning(
                    "Permission denied for viewing unpublished post",
                    extra={
                        "action": "get_post_by_id",
                        "post_id": post_id,
                        "user_id": user.id if user else None,
                        "post_author_id": post.author.id,
                        "service": "PostService",
                    },
                )
                raise PermissionDeniedException(
                    _("You don't have permission to view this post")
                )

        logger.info(
            "Post retrieved successfully",
            extra={
                "action": "get_post_by_id",
                "post_id": post_id,
                "user_id": user.id if user else None,
                "service": "PostService",
            },
        )

        return post

    @staticmethod
    @transaction.atomic
    def create_post(author: User, data: dict[str, Any]) -> Post:
        if not has_permission(
            author, f"{AppPrefixes.BLOG}.{BlogPermission.CREATE_POST.value}"
        ):
            logger.warning(
                "Permission denied for creating post",
                extra={
                    "action": "create_post",
                    "user_id": author.id,
                    "service": "PostService",
                },
            )
            raise PermissionDeniedException(
                _("You don't have permission to create posts")
            )

        # Data validation
        if not data.get("title"):
            raise ValidationException(_("Title is required"))

        if not data.get("content"):
            raise ValidationException(_("Content is required"))

        # Set default values
        data.setdefault("is_published", False)
        data.setdefault("created_at", timezone.now())

        try:
            post = Post.objects.create(author=author, **data)

            logger.info(
                "Post created successfully",
                extra={
                    "action": "create_post",
                    "post_id": post.id,
                    "user_id": author.id,
                    "post_title": post.title,
                    "is_published": post.is_published,
                    "service": "PostService",
                },
            )

            return post

        except Exception as e:
            logger.error(
                "Failed to create post",
                extra={
                    "action": "create_post",
                    "user_id": author.id,
                    "error": str(e),
                    "service": "PostService",
                },
            )
            raise BusinessLogicException(_("Failed to create post"))

    @staticmethod
    @transaction.atomic
    def update_post(post: Post, data: dict[str, Any], user: User) -> Post:
        if not has_permission(
            user, f"{AppPrefixes.BLOG}.{BlogPermission.EDIT_POST.value}"
        ):
            logger.warning(
                "Permission denied for updating post",
                extra={
                    "action": "update_post",
                    "post_id": post.id,
                    "user_id": user.id,
                    "post_author_id": post.author.id,
                    "service": "PostService",
                },
            )
            raise PermissionDeniedException(
                _("You don't have permission to edit this post")
            )

        if "title" in data and not data["title"]:
            raise ValidationException(_("Title cannot be empty"))

        if "content" in data and not data["content"]:
            raise ValidationException(_("Content cannot be empty"))

        if data.get("is_published", False) and not post.is_published:
            if not has_permission(
                user, f"{AppPrefixes.BLOG}.{BlogPermission.PUBLISH_POST.value}"
            ):
                raise PermissionDeniedException(
                    _("You don't have permission to publish this post")
                )

        old_values = {}
        for key, value in data.items():
            if hasattr(post, key):
                old_values[key] = getattr(post, key)
                setattr(post, key, value)

        post.updated_at = timezone.now()
        post.save()

        logger.info(
            "Post updated successfully",
            extra={
                "action": "update_post",
                "post_id": post.id,
                "user_id": user.id,
                "updated_fields": list(data.keys()),
                "old_values": old_values,
                "new_values": data,
                "service": "PostService",
            },
        )

        return post

    @staticmethod
    @transaction.atomic
    def delete_post(post: Post, user: User) -> None:
        if not has_permission(
            user, f"{AppPrefixes.BLOG}.{BlogPermission.DELETE_POST.value}"
        ):
            logger.warning(
                "Permission denied for deleting post",
                extra={
                    "action": "delete_post",
                    "post_id": post.id,
                    "user_id": user.id,
                    "post_author_id": post.author.id,
                    "service": "PostService",
                },
            )
            raise PermissionDeniedException(
                _("You don't have permission to delete this post")
            )

        post_id = post.id
        post_title = post.title

        post.delete()

        logger.info(
            "Post deleted successfully",
            extra={
                "action": "delete_post",
                "post_id": post_id,
                "post_title": post_title,
                "user_id": user.id,
                "service": "PostService",
            },
        )

    @staticmethod
    def publish_post(post: Post, user: User) -> Post:
        if post.is_published:
            raise BusinessLogicException(_("Post is already published"))

        return PostService.update_post(post, {"is_published": True}, user)

    @staticmethod
    def unpublish_post(post: Post, user: User) -> Post:
        if not post.is_published:
            raise BusinessLogicException(_("Post is already unpublished"))

        return PostService.update_post(post, {"is_published": False}, user)
