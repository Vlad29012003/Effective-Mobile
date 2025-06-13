from django.contrib.auth import get_user_model
from django.core.cache import cache
from faker import Faker
from rest_framework.test import APITestCase

User = get_user_model()


class BaseTestCase(APITestCase):
    def setUp(self):
        self.faker = Faker()


class SessionAuthTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="tester", password="secret")
        logged_in = self.client.login(username="tester", password="secret")
        assert logged_in, "Failed to log in the test user"

    def tearDown(self):
        self.user.delete()
        cache.clear()
        super().tearDown()
