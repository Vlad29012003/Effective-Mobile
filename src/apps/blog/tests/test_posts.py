import random
from unittest.mock import patch, MagicMock

from django.http import HttpResponse
from django.urls import reverse
from django.forms.models import model_to_dict
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework import status

from apps.blog.models import Post
from apps.blog.serializers import PostSerializer
from apps.common.factories import PostFactory
from apps.common.mixins import BaseTestCase, SessionAuthMixin


class PostListTest(SessionAuthMixin, BaseTestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        """
        Set up test data for Post list tests.
        """
        cls.posts: list[Post] = PostFactory.create_batch(size=25)
        return super().setUpTestData()

    def test_list(self) -> None:
        """
        Test that the post list endpoint returns a paginated list of published posts.
        """
        response: HttpResponse = self.client.get(
            path=reverse("post-list", query={"limit": 10, "offset": 0})
        )
        self.check_200_response(response)

        queryset = (
            Post.objects.filter(is_published=True)
            .filter(is_published=True)
            .select_related("author")
        )
        serializer = PostSerializer(instance=queryset, many=True)

        expected_response: Response = self.response_builder.build_200_response(
            serializer.data, response.wsgi_request
        )
        self.assertResponseEqual(response, expected_response)

    def test_filter_by_author(self) -> None:
        """
        Test that the post list endpoint can filter posts by author username.
        """
        random_author_username: str = random.choice(
            [post.author.username for post in self.posts if post.is_published]
        )
        response: HttpResponse = self.client.get(
            path=reverse(
                "post-list",
                query={
                    "limit": 10,
                    "offset": 0,
                    "author__username": random_author_username,
                },
            )
        )
        self.check_200_response(response)

        queryset = (
            Post.objects.filter(is_published=True)
            .filter(is_published=True, author__username=random_author_username)
            .select_related("author")
        )
        serializer = PostSerializer(instance=queryset, many=True)

        expected_response: Response = self.response_builder.build_200_response(
            serializer.data, response.wsgi_request
        )
        self.assertResponseEqual(response, expected_response)

    def test_empty_response(self) -> None:
        """
        Test that the post list endpoint returns an empty list for a non-existent author.
        """
        response: HttpResponse = self.client.get(
            path=reverse("post-list", query={"author__username": "fake_username_1234"})
        )
        self.check_200_response(response)

        expected_response: Response = self.response_builder.build_200_response(
            [], response.wsgi_request
        )
        self.assertResponseEqual(response, expected_response)

    def test_my_posts(self) -> None:
        """
        Test that the endpoint returns only posts authored by the current user.
        """
        self.posts.extend(PostFactory.create_batch(size=5, author=self.user))
        response: HttpResponse = self.client.get(path=reverse("post-my-posts"))
        self.check_200_response(response)
        self.assertTrue(
            all(
                [
                    post["author_id"] == self.user.id
                    for post in response.json()["results"]
                ]
            ),
            "All posts should belong to the current user",
        )

        queryset = Post.objects.filter(author=self.user).select_related("author")
        serializer = PostSerializer(instance=queryset, many=True)

        expected_response: Response = self.response_builder.build_200_response(
            serializer.data, response.wsgi_request
        )
        self.assertResponseEqual(response, expected_response)

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Clean up all Post objects after tests.
        """
        Post.objects.all().delete()
        super().tearDownClass()


class PostRetrieveTest(SessionAuthMixin, BaseTestCase):
    def test_retrieve(self) -> None:
        """
        Test that a published post can be retrieved by its ID.
        """
        post: Post = PostFactory(is_published=True)
        response: HttpResponse = self.client.get(
            path=reverse("post-detail", kwargs={"pk": post.id})
        )
        self.check_200_response(response)

        serializer = PostSerializer(instance=post)

        expected_response: Response = self.response_builder.build_200_response(
            serializer.data, response.wsgi_request, many=False
        )
        self.assertResponseEqual(response, expected_response)

    def test_retrieve_not_published(self) -> None:
        """
        Test that retrieving an unpublished post returns a 403 Forbidden response.
        """
        post: Post = PostFactory(is_published=False)
        response: HttpResponse = self.client.get(
            path=reverse("post-detail", kwargs={"pk": post.id})
        )

        self.check_403_response(response)

        expected_response: Response = self.response_builder.build_error(
            status=status.HTTP_403_FORBIDDEN,
            message="You don't have permission to view this post",
            errors=[],
        )
        self.assertResponseEqual(response, expected_response)

    def test_retrieve_nonexistent(self) -> None:
        """
        Test that retrieving a non-existent post returns a 404 Not Found response.
        """
        response: HttpResponse = self.client.get(
            path=reverse("post-detail", kwargs={"pk": 9999})
        )

        self.check_404_response(response)

        expected_response: Response = self.response_builder.build_404_response(
            NotFound("No Post matches the given query.")
        )
        self.assertResponseEqual(response, expected_response)

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Clean up all Post objects after tests.
        """
        Post.objects.all().delete()
        super().tearDownClass()


class PostCreateTest(SessionAuthMixin, BaseTestCase):
    @patch("apps.blog.services.has_permission")
    def test_create(self, mock_has_permission: MagicMock) -> None:
        """
        Test that an authenticated user can create a post with proper permissions.
        """
        mock_has_permission.return_value = True
        post_data = model_to_dict(PostFactory.build(), exclude=["author", "id"])

        response: HttpResponse = self.client.post(
            path=reverse("post-list"), data=post_data
        )
        self.check_201_response(response)

        queryset = Post.objects.filter(
            author=self.user,
            title=post_data["title"],
            is_published=post_data["is_published"],
        )

        self.assertTrue(
            queryset.exists(), "Post should be created and exist in the database"
        )
        serializer = PostSerializer(instance=queryset.first())

        expected_response: Response = self.response_builder.build_201_response(
            serializer.data, response.wsgi_request
        )
        self.assertResponseEqual(response, expected_response)

        mock_has_permission.assert_called_once()

    @patch("apps.blog.services.has_permission")
    def test_create_without_permissions(self, mock_has_permission: MagicMock) -> None:
        """
        Test that creating a post fails when user lacks the required permissions.
        """
        mock_has_permission.return_value = False
        post_data = model_to_dict(PostFactory.build(), exclude=["author", "id"])

        response: HttpResponse = self.client.post(
            path=reverse("post-list"), data=post_data
        )
        self.check_403_response(response)

        expected_response: Response = self.response_builder.build_error(
            status=status.HTTP_403_FORBIDDEN,
            message="You don't have permission to create posts",
            errors=[],
        )
        self.assertResponseEqual(response, expected_response)

        mock_has_permission.assert_called_once()

    def test_create_with_invalid_data(self) -> None:
        """
        Test that creating a post fails with invalid data (missing required fields).
        """
        post_data = model_to_dict(
            PostFactory.build(), exclude=["author", "id", "title"]
        )

        response: HttpResponse = self.client.post(
            path=reverse("post-list"), data=post_data
        )
        self.check_422_response(response)

        expected_response: Response = self.response_builder.build_error(
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Validation failed",
            errors=[
                {
                    "code": "required",
                    "detail": "This field is required.",
                    "attr": "title",
                }
            ],
        )
        self.assertResponseEqual(response, expected_response)

    def test_create_without_login(self) -> None:
        """
        Test that creating a post fails when user is not authenticated.
        """
        self.client.logout()
        post_data = model_to_dict(PostFactory.build(), exclude=["author", "id"])

        response: HttpResponse = self.client.post(
            path=reverse("post-list"), data=post_data
        )
        self.check_403_response(response)

        expected_response: Response = self.response_builder.build_error(
            status=status.HTTP_403_FORBIDDEN,
            message="Permission denied",
            errors=[
                {
                    "code": "permission_denied",
                    "detail": "Authentication credentials were not provided.",
                }
            ],
        )
        self.assertResponseEqual(response, expected_response)


class PostUpdateTest(SessionAuthMixin, BaseTestCase):
    @patch("apps.blog.services.has_permission")
    def test_update(self, mock_has_permission: MagicMock) -> None:
        """
        Test that a user can update their own post with proper permissions.
        """
        post: Post = PostFactory.create(author=self.user)
        data_to_update = model_to_dict(PostFactory.build(), exclude=["author", "id"])

        mock_has_permission.return_value = True

        response: HttpResponse = self.client.put(
            path=reverse("post-detail", kwargs={"pk": post.id}), data=data_to_update
        )
        self.check_200_response(response)

        post.refresh_from_db()

        for key, value in data_to_update.items():
            self.assertTrue(hasattr(post, key), f"Post should have attribute '{key}'")
            self.assertEqual(
                getattr(post, key),
                value,
                f"Post attribute '{key}' should be updated to '{value}'",
            )

        serializer = PostSerializer(instance=post)
        expected_response: Response = self.response_builder.build_200_response(
            data=serializer.data, request=response.wsgi_request, many=False
        )
        self.assertResponseEqual(response, expected_response)

    @patch("apps.blog.services.has_permission")
    def test_update_without_permission(self, mock_has_permission: MagicMock) -> None:
        """
        Test that updating a post fails when user lacks the required permissions.
        """
        post: Post = PostFactory.create(author=self.user, is_published=True)
        data_to_update = model_to_dict(
            PostFactory.build(is_published=False), exclude=["author", "id"]
        )

        mock_has_permission.side_effect = (False, False)

        response: HttpResponse = self.client.put(
            path=reverse("post-detail", kwargs={"pk": post.id}), data=data_to_update
        )
        self.check_403_response(response)

        for key, value in data_to_update.items():
            self.assertTrue(hasattr(post, key), f"Post should have attribute '{key}'")
            self.assertNotEqual(
                getattr(post, key),
                value,
                f"Post attribute '{key}' should not be updated to '{value}' without permission",
            )

        expected_response: Response = self.response_builder.build_error(
            status=status.HTTP_403_FORBIDDEN,
            message="You don't have permission to edit this post",
            errors=[],
        )
        self.assertResponseEqual(response, expected_response)

    def test_update_nonexistent(self) -> None:
        """
        Test that updating a non-existent post returns a 404 error.
        """
        data_to_update = model_to_dict(PostFactory.build(), exclude=["author", "id"])

        response: HttpResponse = self.client.put(
            path=reverse("post-detail", kwargs={"pk": 99999}), data=data_to_update
        )
        self.check_404_response(response)

        expected_response: Response = self.response_builder.build_404_response(
            NotFound("No Post matches the given query.")
        )
        self.assertResponseEqual(response, expected_response)

    def test_update_foreign(self) -> None:
        """
        Test that updating another user's post fails with a 403 error.
        """
        post: Post = PostFactory.create(is_published=True)
        data_to_update = model_to_dict(
            PostFactory.build(is_published=False), exclude=["author", "id"]
        )

        response: HttpResponse = self.client.put(
            path=reverse("post-detail", kwargs={"pk": post.id}), data=data_to_update
        )
        self.check_403_response(response)

        for key, value in data_to_update.items():
            self.assertTrue(hasattr(post, key), f"Post should have attribute '{key}'")
            self.assertNotEqual(
                getattr(post, key),
                value,
                f"Post attribute '{key}' should not be updated to '{value}' without permission",
            )

        expected_response: Response = self.response_builder.build_403_response(
            PermissionDenied()
        )
        self.assertResponseEqual(response, expected_response)

    def tearDown(self):
        Post.objects.all().delete()
        return super().tearDown()


class PostDeleteTest(SessionAuthMixin, BaseTestCase):
    @patch("apps.blog.services.has_permission")
    def test_delete(self, mock_has_permission: MagicMock) -> None:
        """
        Test that a user can delete their own post with proper permissions.
        """
        post: Post = PostFactory.create(author=self.user)

        mock_has_permission.return_value = True

        response: HttpResponse = self.client.delete(
            path=reverse("post-detail", kwargs={"pk": post.id})
        )
        self.check_204_response(response)

        self.assertFalse(
            Post.objects.filter(id=post.id).exists(),
            "Post should be deleted from the database",
        )

    @patch("apps.blog.services.has_permission")
    def test_delete_without_permission(self, mock_has_permission: MagicMock) -> None:
        """
        Test that deleting a post fails when user lacks the required permissions.
        """
        post: Post = PostFactory.create(author=self.user, is_published=True)

        mock_has_permission.return_value = False

        response: HttpResponse = self.client.delete(
            path=reverse("post-detail", kwargs={"pk": post.id})
        )
        self.check_403_response(response)

        self.assertTrue(
            Post.objects.filter(id=post.id).exists(),
            "Post should still exist in the database when deletion is not allowed",
        )

        expected_response = self.response_builder.build_error(
            status=status.HTTP_403_FORBIDDEN,
            message="You don't have permission to delete this post",
            errors=[],
        )
        self.assertResponseEqual(response, expected_response)

    def test_delete_foreign(self):
        """
        Test that deleting another user's post fails with a 403 error.
        """
        post: Post = PostFactory.create(is_published=True)

        response: HttpResponse = self.client.delete(
            path=reverse("post-detail", kwargs={"pk": post.id})
        )
        self.check_403_response(response)

        self.assertTrue(
            Post.objects.filter(id=post.id).exists(),
            "Post should still exist in the database when deletion is not allowed",
        )

        expected_response: Response = self.response_builder.build_403_response(
            PermissionDenied()
        )
        self.assertResponseEqual(response, expected_response)

    def test_delete_nonexistent(self):
        """
        Test that deleting a non-existent post returns a 404 error.
        """
        response: HttpResponse = self.client.delete(
            path=reverse("post-detail", kwargs={"pk": 99999})
        )
        self.check_404_response(response)

        expected_response: Response = self.response_builder.build_404_response(
            NotFound("No Post matches the given query.")
        )
        self.assertResponseEqual(response, expected_response)

    def tearDown(self):
        Post.objects.all().delete()
        return super().tearDown()


class PostPublishTest(SessionAuthMixin, BaseTestCase):
    @patch("apps.blog.services.has_permission")
    def test_publish(self, mock_has_permission: MagicMock):
        """
        Test that a user can publish their unpublished post with proper permissions.
        """
        post: Post = PostFactory.create(author=self.user, is_published=False)

        mock_has_permission.side_effect = [True, True]

        response: HttpResponse = self.client.post(
            path=reverse("post-publish", kwargs={"pk": post.id})
        )
        self.check_200_response(response)

        post.refresh_from_db()

        self.assertTrue(
            post.is_published, "Post should be marked as published after publish action"
        )

        serializer = PostSerializer(instance=post)
        expected_response: Response = self.response_builder.build_200_response(
            data=serializer.data, request=response.wsgi_request, many=False
        )
        self.assertResponseEqual(response, expected_response)

    def test_publish_published(self):
        """
        Test that publishing an already published post returns an error.
        """
        post: Post = PostFactory.create(author=self.user, is_published=True)

        response: HttpResponse = self.client.post(
            path=reverse("post-publish", kwargs={"pk": post.id})
        )

        self.check_422_response(response)

        self.assertTrue(
            post.is_published,
            "Post should remain published when trying to publish an already published post",
        )

        expected_response = self.response_builder.build_error(
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Post is already published",
            errors=[],
        )
        self.assertResponseEqual(response, expected_response)

    @patch("apps.blog.services.has_permission")
    def test_publish_without_edit_permission(self, mock_has_permission: MagicMock):
        """
        Test that publishing a post fails when user lacks edit permissions.
        """
        post: Post = PostFactory.create(author=self.user, is_published=False)

        mock_has_permission.side_effect = [False, False]

        response: HttpResponse = self.client.post(
            path=reverse("post-publish", kwargs={"pk": post.id})
        )
        self.check_403_response(response)

        expected_response: Response = self.response_builder.build_error(
            status=status.HTTP_403_FORBIDDEN,
            message="You don't have permission to edit this post",
            errors=[],
        )
        self.assertResponseEqual(response, expected_response)

    @patch("apps.blog.services.has_permission")
    def test_publish_without_publish_permission(self, mock_has_permission: MagicMock):
        """
        Test that publishing a post fails when user lacks publish permissions.
        """
        post: Post = PostFactory.create(author=self.user, is_published=False)

        mock_has_permission.side_effect = [True, False]

        response: HttpResponse = self.client.post(
            path=reverse("post-publish", kwargs={"pk": post.id})
        )
        self.check_403_response(response)

        expected_response: Response = self.response_builder.build_error(
            status=status.HTTP_403_FORBIDDEN,
            message="You don't have permission to publish this post",
            errors=[],
        )
        self.assertResponseEqual(response, expected_response)

    @patch("apps.blog.services.has_permission")
    def test_unpublish(self, mock_has_permission: MagicMock):
        """
        Test that a user can unpublish their published post with proper permissions.
        """
        post: Post = PostFactory.create(author=self.user, is_published=True)

        mock_has_permission.side_effect = [True, True]

        response: HttpResponse = self.client.post(
            path=reverse("post-unpublish", kwargs={"pk": post.id})
        )
        self.check_200_response(response)

        post.refresh_from_db()

        self.assertFalse(
            post.is_published,
            "Post should be marked as unpublished after unpublish action",
        )

        serializer = PostSerializer(instance=post)
        expected_response: Response = self.response_builder.build_200_response(
            serializer.data, response.wsgi_request, many=False
        )
        self.assertResponseEqual(response, expected_response)

    def test_unpublish_unpublished(self):
        """
        Test that unpublishing an already unpublished post returns an error.
        """
        post: Post = PostFactory.create(author=self.user, is_published=False)

        response: HttpResponse = self.client.post(
            path=reverse("post-unpublish", kwargs={"pk": post.id})
        )
        self.check_422_response(response)

        post.refresh_from_db()

        self.assertFalse(
            post.is_published,
            "Post should remain unpublished when trying to unpublish an already unpublished post",
        )

        expected_response: Response = self.response_builder.build_error(
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Post is already unpublished",
            errors=[],
        )
        self.assertResponseEqual(response, expected_response)

    def tearDown(self):
        Post.objects.all().delete()
        return super().tearDown()
