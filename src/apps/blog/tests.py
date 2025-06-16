from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from faker import Faker
from apps.blog.models import Post

User = get_user_model()


class PostAPITestCase(APITestCase):
    def setUp(self):
        """Настройка тестового окружения."""
        self.fake = Faker()

        # Создаем двух пользователей
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')

        # Аутентифицируем первого пользователя
        self.client.force_authenticate(user=self.user1)

        # Получаем JWT токен для user1
        refresh = RefreshToken.for_user(self.user1)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Создаем посты
        self.post1 = Post.objects.create(author=self.user1, title='Post 1 by User1', content='Content 1',
                                         is_published=True)
        self.post2 = Post.objects.create(author=self.user2, title='Post 2 by User2', content='Content 2',
                                         is_published=True)
        self.draft_post = Post.objects.create(author=self.user1, title='Draft by User1', content='Draft Content',
                                              is_published=False)

    def test_list_published_posts(self):
        """Тест: получение списка только опубликованных постов."""
        # Анонимный пользователь тоже может видеть список
        self.client.logout()
        response = self.client.get('/api/blog/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Должно быть 2 опубликованных поста
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['title'], self.post2.title)  # Сортировка по -created_at

    def test_retrieve_post(self):
        """Тест: получение одного поста."""
        response = self.client.get(f'/api/blog/posts/{self.post1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.post1.title)

    def test_create_post_authenticated(self):
        """Тест: создание поста аутентифицированным пользователем."""
        post_data = {
            'title': self.fake.sentence(),
            'content': self.fake.text(),
            'is_published': True
        }
        response = self.client.post('/api/blog/posts/', data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.filter(title=post_data['title']).exists())
        new_post = Post.objects.get(title=post_data['title'])
        self.assertEqual(new_post.author, self.user1)

    def test_create_post_unauthenticated(self):
        """Тест: попытка создания поста неаутентифицированным пользователем."""
        self.client.logout()
        post_data = {'title': 'Test', 'content': 'Test content'}
        response = self.client.post('/api/blog/posts/', data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_own_post(self):
        """Тест: обновление своего поста."""
        updated_data = {'title': 'Updated Title'}
        response = self.client.patch(f'/api/blog/posts/{self.post1.id}/', data=updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Updated Title')

    def test_update_other_users_post(self):
        """Тест: попытка обновления чужого поста."""
        updated_data = {'title': 'Should Not Update'}
        # self.user1 пытается обновить пост self.user2
        response = self.client.patch(f'/api/blog/posts/{self.post2.id}/', data=updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_post(self):
        """Тест: удаление своего поста."""
        response = self.client.delete(f'/api/blog/posts/{self.post1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=self.post1.id).exists())

    def test_delete_other_users_post(self):
        """Тест: попытка удаления чужого поста."""
        response = self.client.delete(f'/api/blog/posts/{self.post2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Post.objects.filter(id=self.post2.id).exists())