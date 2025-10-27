import contextlib
import os
import shutil
import tempfile
import uuid
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from faker import Faker
from rest_framework import exceptions, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APITestCase

from config.additional.error_handling import (
    _handle_not_found,
    _handle_permission_denied,
    _handle_validation_error,
)

User = get_user_model()


class ResponseBuilder:
    @classmethod
    def build_response(cls, data: Any, status: int) -> Response:
        return Response(data=data, status=status)

    @classmethod
    def build_200_response(
        cls, data: list[dict[str, Any]], request: Request | WSGIRequest, many: bool = True
    ) -> Response:
        if isinstance(request, WSGIRequest):
            request = Request(request)

        if many:
            paginator = LimitOffsetPagination()
            paginated_data = paginator.paginate_queryset(data, request)
            response: Response = paginator.get_paginated_response(paginated_data)
            response.status_code = status.HTTP_200_OK
            return response

        return Response(data=data, status=status.HTTP_200_OK)

    @classmethod
    def build_201_response(cls, data: list[dict[str, Any]], request: Request | WSGIRequest) -> Response:
        if isinstance(request, WSGIRequest):
            request = Request(request)

        return Response(data=data, status=status.HTTP_201_CREATED)

    @classmethod
    def build_error(cls, status: int, message: str, errors: list) -> Response:
        return Response(data={"message": message, "errors": errors}, status=status)

    @classmethod
    def build_403_response(cls, exception: exceptions.PermissionDenied) -> Response:
        return _handle_permission_denied(exc=exception)

    @classmethod
    def build_404_response(cls, exception: exceptions.NotFound) -> Response:
        return _handle_not_found(exc=exception)

    @classmethod
    def build_422_response(cls, exception: exceptions.ValidationError) -> Response:
        return _handle_validation_error(exc=exception)


class BaseTestCase(APITestCase):
    response_builder = ResponseBuilder
    maxDiff = None

    def setUp(self):
        self.faker = Faker()

    def check_200_response(self, response: HttpResponse) -> None:
        """
        Check that response status code is 200 OK
        """
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Response status is not 200 OK")

    def check_201_response(self, response: HttpResponse) -> None:
        """
        Check that response status code is 201 CREATED
        """
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Response status is not 201 CREATED")

    def check_204_response(self, response: HttpResponse) -> None:
        """
        Check that response status code is 204 NO CONTENT
        """
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "Response status is not 204 NO CONTENT")

    def check_404_response(self, response: HttpResponse) -> None:
        """
        Check that response status code is 404 NOT FOUND
        """
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, "Response status is not 404 NOT FOUND")

    def check_400_response(self, response: HttpResponse) -> None:
        """
        Check that response status code is 404 BAD REQUEST
        """
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, "Response status is not 400 BAD REQUEST")

    def check_401_response(self, response: HttpResponse) -> None:
        """
        Check that response status code is 401 UNAUTHORIZED
        """
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED, "Response status code is not 401 UNAUTHORIZED"
        )

    def check_403_response(self, response: HttpResponse) -> None:
        """
        Check that response status code is 403 FORBIDDEN
        """
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, "Response status code is not 403 FORBIDDEN")

    def check_422_response(self, response: HttpResponse) -> None:
        """
        Check that response status code is 422 UNPROCESSABLE ENTITY
        """
        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Response status code is not 422 UNPROCESSABLE ENTITY",
        )

    def assertResponseEqual(self, response: HttpResponse | Response, expected_response: Response) -> None:
        if isinstance(response, HttpResponse):
            response = Response(data=response.json(), status=response.status_code)
        self.assertEqual(response.status_code, expected_response.status_code, "Response status codes didn't match")
        self.assertEqual(response.data, expected_response.data, "Response JSON didn't match")


class SessionAuthMixin:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create_user(username="tester", password="secret")

    def setUp(self):
        super().setUp()
        logged_in = self.client.login(username="tester", password="secret")
        assert logged_in, "Failed to log in the test user"

    def tearDown(self):
        cache.clear()
        super().tearDown()


class CleanMinioMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls._backup_storage_settings()
        cls._create_test_storage()

    @classmethod
    def _backup_storage_settings(cls):
        cls._original_bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        cls._original_storage = default_storage

        if hasattr(default_storage, "bucket_name"):
            cls._original_bucket_name = default_storage.bucket_name

    @classmethod
    def _create_test_storage(cls):
        cls.test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"

        settings.AWS_STORAGE_BUCKET_NAME = cls.test_bucket

        if hasattr(default_storage, "bucket_name"):
            default_storage.bucket_name = cls.test_bucket

        if hasattr(default_storage, "_bucket"):
            default_storage._bucket = None

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_test_files()
        cls._restore_storage_settings()
        super().tearDownClass()

    @classmethod
    def _cleanup_test_files(cls):
        try:
            dirs, files = default_storage.listdir("")

            for file_name in files:
                with contextlib.suppress(Exception):
                    default_storage.delete(file_name)

            for dir_name in dirs:
                with contextlib.suppress(Exception):
                    cls._cleanup_directory(dir_name)

        except Exception as e:
            print(f"Failed to cleanup test files: {e}")

    @classmethod
    def _cleanup_directory(cls, directory):
        try:
            dirs, files = default_storage.listdir(directory)

            for file_name in files:
                file_path = f"{directory}/{file_name}"
                with contextlib.suppress(Exception):
                    default_storage.delete(file_path)

            for dir_name in dirs:
                nested_dir = f"{directory}/{dir_name}"
                cls._cleanup_directory(nested_dir)

        except Exception:
            pass

    @classmethod
    def _restore_storage_settings(cls):
        if hasattr(cls, "_original_bucket") and cls._original_bucket:
            settings.AWS_STORAGE_BUCKET_NAME = cls._original_bucket

        if hasattr(cls, "_original_bucket_name") and hasattr(default_storage, "bucket_name"):
            default_storage.bucket_name = cls._original_bucket_name

        if hasattr(default_storage, "_bucket"):
            default_storage._bucket = None


class CleanMediaMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_media_root = tempfile.mkdtemp(prefix="test_media_")
        cls.temp_media_url = f"/test_media_{id(cls)}/"
        cls._original_media_root: str = settings.MEDIA_ROOT
        cls._original_media_url: str = settings.MEDIA_URL

        settings.MEDIA_ROOT = cls.temp_media_root
        settings.MEDIA_URL = cls.temp_media_url

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "_original_media_root"):
            settings.MEDIA_ROOT = cls._original_media_root
            settings.MEDIA_URL = cls._original_media_url

        if hasattr(cls, "temp_media_root") and os.path.exists(cls.temp_media_root):
            try:
                shutil.rmtree(cls.temp_media_root)
            except Exception as e:
                print(f"Failed to cleanup {cls.temp_media_root}: {e}")

        super().tearDownClass()
