from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'content',
            'is_published',
            'author_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'author_username', 'created_at', 'updated_at']

    def create(self, validated_data):
        pass
