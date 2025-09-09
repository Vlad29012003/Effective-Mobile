import logging
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import (
    BusinessLogicException,
    ErrorCodes,
    PermissionDeniedException,
    ResourceNotFoundException,
    ValidationException,
)
from apps.common.permissions import Permission, has_permission

from .models import Post

User: settings.AUTH_USER_MODEL = get_user_model()
logger = logging.getLogger(__name__)


class PostService:
    """
    Сервис для работы с постами блога.

    Содержит всю бизнес-логику для создания, обновления,
    удаления и получения постов с проверкой разрешений.
    """

    @staticmethod
    def get_published_posts() -> list[Post]:
        """
        Получить все опубликованные посты.

        Returns:
            Список опубликованных постов с авторами
        """
        logger.info(
            "Fetching published posts",
            extra={"action": "get_published_posts", "service": "PostService"},
        )

        return list(Post.published.all().select_related("author"))

    @staticmethod
    def get_user_posts(user: User, include_drafts: bool = True) -> list[Post]:
        """
        Получить посты пользователя.

        Args:
            user: Пользователь
            include_drafts: Включать ли черновики

        Returns:
            Список постов пользователя
        """
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
        """
        Получить пост по ID с проверкой разрешений.

        Args:
            post_id: ID поста
            user: Текущий пользователь (для проверки разрешений)

        Returns:
            Пост

        Raises:
            ResourceNotFoundException: Если пост не найден
            PermissionDeniedException: Если нет разрешения на просмотр
        """
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
            raise ResourceNotFoundException("Post not found")

        # Проверяем разрешения на просмотр
        if not post.is_published and user:
            if not has_permission(
                user, Permission.BLOG_VIEW_POST.value, post_author_id=post.author.id
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
                    "You don't have permission to view this post"
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
        """
        Создать новый пост с проверкой разрешений.

        Args:
            author: Автор поста
            data: Данные поста

        Returns:
            Созданный пост

        Raises:
            PermissionDeniedException: Если нет разрешения на создание
            ValidationException: Если данные некорректны
        """
        # Проверяем разрешение на создание поста
        if not has_permission(author, Permission.BLOG_CREATE_POST.value):
            logger.warning(
                "Permission denied for creating post",
                extra={
                    "action": "create_post",
                    "user_id": author.id,
                    "service": "PostService",
                },
            )
            raise PermissionDeniedException("You don't have permission to create posts")

        # Валидация данных
        if not data.get("title"):
            raise ValidationException("Title is required")

        if not data.get("content"):
            raise ValidationException("Content is required")

        # Устанавливаем дефолтные значения
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
            raise BusinessLogicException("Failed to create post")

    @staticmethod
    @transaction.atomic
    def update_post(post: Post, data: dict[str, Any], user: User) -> Post:
        """
        Обновить пост с проверкой разрешений.

        Args:
            post: Пост для обновления
            data: Новые данные
            user: Пользователь, выполняющий обновление

        Returns:
            Обновленный пост

        Raises:
            PermissionDeniedException: Если нет разрешения на редактирование
            ValidationException: Если данные некорректны
        """
        # Проверяем разрешение на редактирование
        if not has_permission(
            user, Permission.BLOG_EDIT_POST.value, post_author_id=post.author.id
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
                "You don't have permission to edit this post"
            )

        # Валидация
        if "title" in data and not data["title"]:
            raise ValidationException("Title cannot be empty")

        if "content" in data and not data["content"]:
            raise ValidationException("Content cannot be empty")

        # Специальная проверка для публикации
        if data.get("is_published", False) and not post.is_published:
            if not has_permission(
                user, Permission.BLOG_PUBLISH_POST.value, post_author_id=post.author.id
            ):
                raise PermissionDeniedException(
                    "You don't have permission to publish this post"
                )

        # Обновляем поля
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
        """
        Удалить пост с проверкой разрешений.

        Args:
            post: Пост для удаления
            user: Пользователь, выполняющий удаление

        Raises:
            PermissionDeniedException: Если нет разрешения на удаление
        """
        # Проверяем разрешение на удаление
        if not has_permission(
            user, Permission.BLOG_DELETE_POST.value, post_author_id=post.author.id
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
                "You don't have permission to delete this post"
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
        """
        Опубликовать пост.

        Args:
            post: Пост для публикации
            user: Пользователь, выполняющий публикацию

        Returns:
            Обновленный пост

        Raises:
            PermissionDeniedException: Если нет разрешения на публикацию
            BusinessLogicException: Если пост уже опубликован
        """
        if post.is_published:
            raise BusinessLogicException("Post is already published")

        return PostService.update_post(post, {"is_published": True}, user)

    @staticmethod
    def unpublish_post(post: Post, user: User) -> Post:
        """
        Снять пост с публикации.

        Args:
            post: Пост для снятия с публикации
            user: Пользователь, выполняющий действие

        Returns:
            Обновленный пост

        Raises:
            PermissionDeniedException: Если нет разрешения
            BusinessLogicException: Если пост не опубликован
        """
        if not post.is_published:
            raise BusinessLogicException("Post is already unpublished")

        return PostService.update_post(post, {"is_published": False}, user)
