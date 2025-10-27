from rest_framework import serializers

from .models import Post


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_id = serializers.IntegerField(source="author.id", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "content",
            "is_published",
            "author_username",
            "author_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author_username",
            "author_id",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """
        Создание поста через сервис происходит в views.
        Этот метод не должен вызываться напрямую.
        """
        raise NotImplementedError("Post creation should be handled through PostService in views")
