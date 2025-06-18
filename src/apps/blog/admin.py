from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Post, PostImage


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ("title", "created_at", "updated_at")
    search_fields = ("title", "content")
    list_filter = ("created_at", "updated_at")


@admin.register(PostImage)
class PostImageAdmin(ModelAdmin):
    list_display = ("post", "image", "created_at")
    search_fields = ("post__title",)
    list_filter = ("created_at",)
