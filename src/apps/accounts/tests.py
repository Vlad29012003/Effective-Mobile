from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class LoginViewTest(APITestCase):
    def setUp(self):
        self.active_user = User.objects.create_user(
            username="active", password="secret", is_active=True
        )
        self.inactive_user = User.objects.create_user(
            username="blocked", password="secret", is_active=False
        )
        self.will_blocked_user = User.objects.create_user(
            username="will_blocked", password="secret", is_active=True
        )
        self.url = reverse("login")

    def tearDown(self):
        self.active_user.delete()
        self.inactive_user.delete()
        self.will_blocked_user.delete()
        cache.clear()
        super().tearDown()

    def test_missing_credentials(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        errors = resp.data.get("errors", [])

        self.assertTrue(any(e["attr"] == "username" for e in errors))
        self.assertTrue(any(e["attr"] == "password" for e in errors))

    def test_user_not_found(self):
        resp = self.client.post(
            self.url, {"username": "nope", "password": "x"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data["detail"], "User not found")

    def test_inactive_user(self):
        resp = self.client.post(
            self.url,
            {"username": self.inactive_user.username, "password": "secret"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data["detail"], "Account is block")

    def test_invalid_credentials(self):
        resp = self.client.post(
            self.url,
            {"username": self.active_user.username, "password": "wrong"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp.data["detail"], "Invalid credentials")

    def test_successful_login_sets_session(self):
        resp = self.client.post(
            self.url,
            {"username": self.active_user.username, "password": "secret"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("sessionid", resp.client.cookies)

    def test_second_login_to_one_account(self):
        client1 = APIClient()
        client2 = APIClient()

        resp = client1.post(
            self.url,
            {"username": self.active_user.username, "password": "secret"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        session_id = resp.client.cookies["sessionid"].value

        session_before_login = Session.objects.get(session_key=session_id)
        session_expire_date = session_before_login.expire_date

        resp = client2.post(
            self.url,
            {"username": self.active_user.username, "password": "secret"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        session_after_login = Session.objects.get(session_key=session_id)

        self.assertNotEqual(session_after_login.expire_date, session_expire_date)

    def test_block_user_after_three_failed_logins(self):
        test_cases = [
            (0, True, status.HTTP_401_UNAUTHORIZED),
            (1, True, status.HTTP_401_UNAUTHORIZED),
            (2, False, status.HTTP_401_UNAUTHORIZED),
            (3, False, status.HTTP_403_FORBIDDEN),
        ]

        for attempt, expected_active, expected_status in test_cases:
            with self.subTest(attempt=attempt):
                resp = self.client.post(
                    self.url,
                    {"username": self.will_blocked_user.username, "password": "wrong"},
                    format="json",
                )
                self.will_blocked_user.refresh_from_db()

                self.assertEqual(
                    self.will_blocked_user.is_active,
                    expected_active,
                    f"Attempt {attempt}: expected is_active={expected_active}",
                )
                self.assertEqual(
                    resp.status_code,
                    expected_status,
                    f"Attempt {attempt}: expected HTTP {expected_status}",
                )
