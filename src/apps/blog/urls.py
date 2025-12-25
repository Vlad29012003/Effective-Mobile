from django.urls import path

from apps.blog.views import PostDetailView, PostListView

app_name = "blog"

urlpatterns = [
    path("posts/", PostListView.as_view(), name="post-list"),
    path("posts/<int:post_id>/", PostDetailView.as_view(), name="post-detail"),
]
