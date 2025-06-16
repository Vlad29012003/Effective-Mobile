from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from apps.blog.models import Post

User = get_user_model()


class PostAPITestCase(APITestCase):
    def setUp(self):
        """Настройка тестового окружения."""
        self.fake = Faker()

        self.user1 = User.objects.create_user(username="user1", password="password123")
        self.user2 = User.objects.create_user(username="user2", password="password123")

        self.client.force_authenticate(user=self.user1)

        self.posts_url = reverse("post-list")  # Returns the URL for the post list view

    def post_detail_url(self, pk):
        """Helper для получения URL детализации поста."""
        return reverse("post-detail", kwargs={"pk": pk})

    def _create_sample_posts(self):
        """Helper to create posts, called after URL setup."""
        self.post1 = Post.objects.create(
            author=self.user1,
            title="Post 1 by User1",
            content="Content 1",
            is_published=True,
        )
        self.post2 = Post.objects.create(
            author=self.user2,
            title="Post 2 by User2",
            content="Content 2",
            is_published=True,
        )
        self.draft_post = Post.objects.create(
            author=self.user1,
            title="Draft by User1",
            content="Draft Content",
            is_published=False,
        )

    @classmethod
    def setUpTestData(cls):
        """
        Создание объектов, которые не будут изменяться в тестах.
        Выполняется один раз для класса.
        """
        cls.user1_data = {"username": "user1_setup", "password": "password123"}
        cls.user2_data = {"username": "user2_setup", "password": "password123"}

    def test_list_published_posts(self):
        """Тест: получение списка только опубликованных постов."""
        self._create_sample_posts()

        self.client.logout()

        response = self.client.get(self.posts_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"][0]["title"], self.post2.title)

    def test_retrieve_post(self):
        """Тест: получение одного поста."""
        self._create_sample_posts()

        response = self.client.get(self.post_detail_url(self.post1.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.post1.title)

    def test_create_post_authenticated(self):
        """Тест: создание поста аутентифицированным пользователем."""
        post_data = {
            "title": self.fake.sentence(nb_words=5),  # Faker used here for dynamic data
            "content": self.fake.text(),
            "is_published": True,
        }
        response = self.client.post(self.posts_url, data=post_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.filter(title=post_data["title"]).exists())

        new_post = Post.objects.get(title=post_data["title"])

        self.assertEqual(new_post.author, self.user1)

    def test_create_post_unauthenticated(self):
        """Тест: попытка создания поста неаутентифицированным пользователем."""
        self.client.logout()

        post_data = {"title": "Test Unauth", "content": "Test content unauth"}
        response = self.client.post(self.posts_url, data=post_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_own_post(self):
        """Тест: обновление своего поста."""
        self._create_sample_posts()

        updated_data = {"title": "Updated Title for Own Post"}
        response = self.client.patch(
            self.post_detail_url(self.post1.id), data=updated_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.post1.refresh_from_db()

        self.assertEqual(self.post1.title, updated_data["title"])

    def test_update_other_users_post(self):
        """Тест: попытка обновления чужого поста."""
        self._create_sample_posts()

        updated_data = {"title": "Should Not Update This"}
        response = self.client.patch(
            self.post_detail_url(self.post2.id), data=updated_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.post2.refresh_from_db()

        self.assertNotEqual(self.post2.title, updated_data["title"])

    def test_delete_own_post(self):
        """Тест: удаление своего поста."""
        self._create_sample_posts()

        post_id_to_delete = self.post1.id
        response = self.client.delete(self.post_detail_url(post_id_to_delete))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=post_id_to_delete).exists())

    def test_delete_other_users_post(self):
        """Тест: попытка удаления чужого поста."""
        self._create_sample_posts()

        response = self.client.delete(self.post_detail_url(self.post2.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Post.objects.filter(id=self.post2.id).exists())
