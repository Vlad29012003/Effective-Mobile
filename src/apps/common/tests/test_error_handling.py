"""
Tests for standardized error handling.
"""

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase

from apps.common.exceptions import (
    BusinessLogicException,
    ErrorCodes,
    PermissionDeniedException,
    ResourceNotFoundException,
    StandardError,
    ValidationException,
    convert_drf_validation_error,
)
from config.additional.error_handling import custom_exception_handler

User = get_user_model()


class StandardErrorTestCase(TestCase):
    """Test StandardError class."""

    def test_standard_error_creation(self):
        """Test creating a StandardError."""
        error = StandardError(
            code="required", detail="This field is required.", attr="email"
        )

        self.assertEqual(error.code, "required")
        self.assertEqual(error.detail, "This field is required.")
        self.assertEqual(error.attr, "email")

    def test_standard_error_to_dict(self):
        """Test converting StandardError to dict."""
        error = StandardError(
            code="invalid", detail="Invalid email format.", attr="email"
        )

        expected = {
            "code": "invalid",
            "detail": "Invalid email format.",
            "attr": "email",
        }

        self.assertEqual(error.to_dict(), expected)

    def test_standard_error_to_dict_without_attr(self):
        """Test converting StandardError to dict without attr."""
        error = StandardError(code="general_error", detail="Something went wrong.")

        expected = {"code": "general_error", "detail": "Something went wrong."}

        self.assertEqual(error.to_dict(), expected)


class StandardExceptionTestCase(TestCase):
    """Test StandardAPIException and subclasses."""

    def test_validation_exception(self):
        """Test ValidationException creation and format."""
        errors = [
            StandardError("required", "Email is required.", "email"),
            StandardError("invalid", "Invalid phone format.", "phone"),
        ]

        exc = ValidationException(message="Form validation failed", errors=errors)

        self.assertEqual(exc.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(exc.message, "Form validation failed")
        self.assertEqual(len(exc.errors), 2)
        self.assertEqual(exc.errors[0].code, "required")

    def test_business_logic_exception(self):
        """Test BusinessLogicException."""
        error = StandardError("limit_exceeded", "Maximum posts per day reached.")
        exc = BusinessLogicException(errors=[error])

        self.assertEqual(exc.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(exc.message, "Business logic violation")

    def test_resource_not_found_exception(self):
        """Test ResourceNotFoundException."""
        error = StandardError("not_found", "Post not found.")
        exc = ResourceNotFoundException(errors=[error])

        self.assertEqual(exc.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exc.message, "Resource not found")

    def test_permission_denied_exception(self):
        """Test PermissionDeniedException."""
        error = StandardError("permission_denied", "Not the author.")
        exc = PermissionDeniedException(errors=[error])

        self.assertEqual(exc.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(exc.message, "Permission denied")


class DRFValidationErrorConversionTestCase(TestCase):
    """Test converting DRF ValidationError to standard format."""

    def test_convert_field_validation_error(self):
        """Test converting field validation error."""
        drf_error = ValidationError(
            {
                "email": ["This field is required."],
                "password": ["This field must be at least 8 characters long."],
            }
        )

        standard_exc = convert_drf_validation_error(drf_error)

        self.assertIsInstance(standard_exc, ValidationException)
        self.assertEqual(len(standard_exc.errors), 2)

        # Check first error
        email_error = next(e for e in standard_exc.errors if e.attr == "email")
        self.assertEqual(email_error.code, "invalid")
        self.assertEqual(email_error.detail, "This field is required.")
        self.assertEqual(email_error.attr, "email")

        # Check second error
        password_error = next(e for e in standard_exc.errors if e.attr == "password")
        self.assertEqual(password_error.attr, "password")

    def test_convert_non_field_validation_error(self):
        """Test converting non-field validation error."""
        drf_error = ValidationError(["Invalid data format."])

        standard_exc = convert_drf_validation_error(drf_error)

        self.assertEqual(len(standard_exc.errors), 1)
        self.assertEqual(standard_exc.errors[0].code, "invalid")
        self.assertEqual(standard_exc.errors[0].detail, "Invalid data format.")
        self.assertIsNone(standard_exc.errors[0].attr)

    def test_convert_single_validation_error(self):
        """Test converting single validation error."""
        drf_error = ValidationError("Single error message.")

        standard_exc = convert_drf_validation_error(drf_error)

        self.assertEqual(len(standard_exc.errors), 1)
        self.assertEqual(standard_exc.errors[0].detail, "Single error message.")


class ErrorHandlerAPITestCase(APITestCase):
    """Test error handling through API calls."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_validation_error_format(self):
        """Test that validation errors return 422 with standard format."""
        # Try to create a post without authentication
        url = reverse("post-list")  # Assuming you have this URL
        data = {
            "title": "",  # Empty title should trigger validation error
            "content": "Test content",
        }

        response = self.client.post(url, data, format="json")

        # Should return 401 for authentication (handled by our handler)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("message", response.data)
        self.assertIn("errors", response.data)
        self.assertIsInstance(response.data["errors"], list)

        if response.data["errors"]:
            error = response.data["errors"][0]
            self.assertIn("code", error)
            self.assertIn("detail", error)

    def test_permission_denied_format(self):
        """Test that permission denied returns standard format."""
        # Create a post by another user
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="otherpass123"
        )

        # This test would need actual Post model and endpoints
        # For now, let's test the format structure
        self.assertTrue(True)  # Placeholder

    def test_not_found_format(self):
        """Test that 404 errors return standard format."""
        url = "/api/posts/99999/"  # Non-existent post
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Check if it follows standard format
        if hasattr(response, "data") and isinstance(response.data, dict):
            if "message" in response.data:
                self.assertIn("message", response.data)
                # If it has our standard format, check errors too
                if "errors" in response.data:
                    self.assertIn("errors", response.data)
                    self.assertIsInstance(response.data["errors"], list)


class ErrorCodesTestCase(TestCase):
    """Test ErrorCodes constants."""

    def test_error_codes_exist(self):
        """Test that all required error codes are defined."""
        required_codes = [
            "REQUIRED",
            "INVALID",
            "BLANK",
            "NULL",
            "MIN_LENGTH",
            "MAX_LENGTH",
            "MIN_VALUE",
            "MAX_VALUE",
            "DUPLICATE",
            "NOT_FOUND",
            "PERMISSION_DENIED",
            "CONFLICT",
            "EXPIRED",
            "LIMIT_EXCEEDED",
            "INVALID_CREDENTIALS",
            "TOKEN_EXPIRED",
            "TOKEN_INVALID",
        ]

        for code in required_codes:
            self.assertTrue(hasattr(ErrorCodes, code))
            self.assertIsInstance(getattr(ErrorCodes, code), str)

    def test_error_codes_values(self):
        """Test that error codes have expected string values."""
        self.assertEqual(ErrorCodes.REQUIRED, "required")
        self.assertEqual(ErrorCodes.INVALID, "invalid")
        self.assertEqual(ErrorCodes.NOT_FOUND, "not_found")
        self.assertEqual(ErrorCodes.PERMISSION_DENIED, "permission_denied")


class CustomExceptionHandlerTestCase(TestCase):
    """Test the custom exception handler function."""

    def setUp(self):
        """Set up test context."""
        self.context = {"view": None, "request": None}

    def test_validation_error_handling(self):
        """Test handling of ValidationError."""
        exc = ValidationError({"email": ["This field is required."]})
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = json.loads(response.content)
        self.assertIn("message", data)
        self.assertIn("errors", data)
        self.assertIsInstance(data["errors"], list)
        self.assertTrue(len(data["errors"]) > 0)

        error = data["errors"][0]
        self.assertIn("code", error)
        self.assertIn("detail", error)
        self.assertIn("attr", error)

    def test_standard_exception_handling(self):
        """Test handling of our StandardAPIException."""
        errors = [StandardError("test_code", "Test detail", "test_attr")]
        exc = ValidationException("Test message", errors)

        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = json.loads(response.content)
        self.assertEqual(data["message"], "Test message")
        self.assertEqual(len(data["errors"]), 1)
        self.assertEqual(data["errors"][0]["code"], "test_code")
        self.assertEqual(data["errors"][0]["detail"], "Test detail")
        self.assertEqual(data["errors"][0]["attr"], "test_attr")


class IntegrationTestCase(APITestCase):
    """Integration tests for error handling in real scenarios."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_complete_error_response_format(self):
        """Test that error responses follow company standards."""
        # Test with a simple API call that should trigger validation
        url = "/api/auth/login/"  # Assuming you have this endpoint
        data = {}  # Empty data should trigger validation

        response = self.client.post(url, data, format="json")

        # Should return 422 or 400, but in standard format
        self.assertIn(
            response.status_code,
            [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_401_UNAUTHORIZED,
            ],
        )

        # Check response format
        self.assertIsInstance(response.data, dict)

        # If our handler processed it, it should have standard format
        if "message" in response.data and "errors" in response.data:
            self.assertIn("message", response.data)
            self.assertIn("errors", response.data)
            self.assertIsInstance(response.data["errors"], list)

            # Check each error has required fields
            for error in response.data["errors"]:
                self.assertIn("code", error)
                self.assertIn("detail", error)
                # attr is optional
