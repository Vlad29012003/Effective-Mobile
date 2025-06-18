from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.blog.manager import PostManager
from apps.common.models import TimestampMixin

User: settings.AUTH_USER_MODEL = get_user_model()


class Post(TimestampMixin):
    author: User = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="blog_posts",
        verbose_name=_("Author"),
    )
    title = models.CharField(_("Title"), max_length=200)
    content = models.TextField(_("Content"))
    is_published = models.BooleanField(_("Is Published"), default=False)
    created_at = models.DateTimeField(_("Date Created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date Updated"), auto_now=True)

    objects = models.Manager()
    published = PostManager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")

    def __str__(self):
        return self.title


class PostImage(TimestampMixin):
    post: Post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Post"),
    )
    image = models.ImageField(_("Image"), upload_to="blog_images/")
    caption = models.CharField(_("Caption"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Post Image")
        verbose_name_plural = _("Post Images")

    def __str__(self):
        return f"Image for {self.post.title}"
