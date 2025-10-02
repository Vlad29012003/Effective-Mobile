from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.http import HttpResponse

from apps.common.mixins import BaseTestCase
from apps.common.factories import UserFactory

User = get_user_model()


class LoginViewTest(BaseTestCase):
    def setUp(self):
        self.client.logout()
        self.active_user: User = UserFactory.create(
            username="active", password="secret", is_active=True
        )
        self.inactive_user: User = UserFactory.create(
            username="blocked", password="secret", is_active=False
        )
        self.will_blocked_user: User = UserFactory.create(
            username="will_blocked", password="secret", is_active=True
        )

    def tearDown(self):
        self.active_user.delete()
        self.inactive_user.delete()
        self.will_blocked_user.delete()
        cache.clear()
        super().tearDown()

    def test_missing_credentials(self):
        response: HttpResponse = self.client.post(path=reverse("login"))
        self.check_422_response(response)

        expected_response = self.response_builder.build_error(
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Validation failed",
            errors=[
                {
                    "code": "required",
                    "detail": "This field is required.",
                    "attr": "username",
                },
                {
                    "code": "required",
                    "detail": "This field is required.",
                    "attr": "password",
                },
            ],
        )
        self.assertResponseEqual(response, expected_response)

    def test_user_not_found(self):
        response: HttpResponse = self.client.post(
            path=reverse("login"), data={"username": "nope", "password": "x"}
        )
        self.check_404_response(response)

        expected_response = self.response_builder.build_response(
            status=status.HTTP_404_NOT_FOUND, data={"detail": "User not found"}
        )
        self.assertResponseEqual(response, expected_response)

    def test_inactive_user(self):
        response: HttpResponse = self.client.post(
            path=reverse("login"),
            data={"username": self.inactive_user.username, "password": "secret"},
        )
        self.check_403_response(response)

        expected_response = self.response_builder.build_response(
            status=status.HTTP_403_FORBIDDEN, data={"detail": "Account is block"}
        )
        self.assertResponseEqual(response, expected_response)

    def test_invalid_credentials(self):
        response: HttpResponse = self.client.post(
            path=reverse("login"),
            data={"username": self.active_user.username, "password": "wrong"},
        )
        self.check_401_response(response)

        expected_response = self.response_builder.build_response(
            status=status.HTTP_401_UNAUTHORIZED, data={"detail": "Invalid credentials"}
        )
        self.assertResponseEqual(response, expected_response)

    def test_successful_login_sets_session(self):
        response: HttpResponse = self.client.post(
            path=reverse("login"),
            data={"username": self.active_user.username, "password": "secret"},
        )
        self.check_200_response(response)

        self.assertIn("sessionid", response.client.cookies)

        expected_response = self.response_builder.build_response(
            status=status.HTTP_200_OK, data={"detail": "Login successful"}
        )
        self.assertResponseEqual(response, expected_response)

    def test_second_login_to_one_account(self):
        client1 = APIClient()
        client2 = APIClient()

        response: HttpResponse = client1.post(
            path=reverse("login"),
            data={"username": self.active_user.username, "password": "secret"},
        )
        self.check_200_response(response)

        session_id: str = response.client.cookies["sessionid"].value

        session_before_login = Session.objects.get(session_key=session_id)
        session_expire_date: datetime = session_before_login.expire_date

        response: HttpResponse = client2.post(
            path=reverse("login"),
            data={"username": self.active_user.username, "password": "secret"},
        )
        self.check_200_response(response)

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
                response: HttpResponse = self.client.post(
                    path=reverse("login"),
                    data={
                        "username": self.will_blocked_user.username,
                        "password": "wrong",
                    },
                )
                self.will_blocked_user.refresh_from_db()

                self.assertEqual(
                    self.will_blocked_user.is_active,
                    expected_active,
                    f"Attempt {attempt}: expected is_active={expected_active}",
                )
                self.assertEqual(
                    response.status_code,
                    expected_status,
                    f"Attempt {attempt}: expected HTTP {expected_status}",
                )
