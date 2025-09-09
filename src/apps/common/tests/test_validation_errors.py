"""
Detailed tests for validation error handling and 422 responses.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.common.exceptions import convert_drf_validation_error
from config.additional.error_handling import custom_exception_handler

from .test_error_serializers import (
    TestBusinessLogicSerializer,
    TestValidationSerializer,
)


class SerializerValidationTestCase(TestCase):
    """Test validation errors from serializers."""

    def test_required_field_errors(self):
        """Test required field validation errors."""
        serializer = TestValidationSerializer(data={})

        self.assertFalse(serializer.is_valid())

        # Convert to our standard format
        drf_error = ValidationError(serializer.errors)
        standard_exc = convert_drf_validation_error(drf_error)

        self.assertEqual(len(standard_exc.errors), 4)  # 4 required fields

        # Check that each error has proper format
        for error in standard_exc.errors:
            self.assertIn(error.code, ["required", "invalid"])
            self.assertIsNotNone(error.detail)
            self.assertIsNotNone(error.attr)

    def test_invalid_email_format(self):
        """Test invalid email format error."""
        data = {
            "email": "invalid-email",
            "age": 25,
            "password": "password123",
            "username": "testuser",
        }

        serializer = TestValidationSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        # Convert to standard format
        drf_error = ValidationError(serializer.errors)
        standard_exc = convert_drf_validation_error(drf_error)

        # Find email error
        email_error = next(e for e in standard_exc.errors if e.attr == "email")
        self.assertEqual(email_error.code, "invalid")
        self.assertIn("email", email_error.detail.lower())

    def test_min_max_value_errors(self):
        """Test min/max value validation errors."""
        data = {
            "email": "test@example.com",
            "age": -5,  # Below minimum
            "password": "123",  # Too short
            "username": "testuser",
        }

        serializer = TestValidationSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        drf_error = ValidationError(serializer.errors)
        standard_exc = convert_drf_validation_error(drf_error)

        # Find age error
        age_error = next(e for e in standard_exc.errors if e.attr == "age")
        self.assertEqual(age_error.code, "min_value")

        # Find password error
        password_error = next(e for e in standard_exc.errors if e.attr == "password")
        self.assertEqual(password_error.code, "min_length")

    def test_custom_validation_errors(self):
        """Test custom validation errors with custom codes."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        User.objects.create_user(
            username="existing", email="existing@example.com", password="password123"
        )

        data = {
            "email": "existing@example.com",  # Duplicate email
            "age": 25,
            "password": "password123",
            "username": "   ",  # Blank username
        }

        serializer = TestValidationSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        drf_error = ValidationError(serializer.errors)
        standard_exc = convert_drf_validation_error(drf_error)

        # Find custom validation errors
        email_error = next(e for e in standard_exc.errors if e.attr == "email")
        username_error = next(e for e in standard_exc.errors if e.attr == "username")

        self.assertEqual(email_error.code, "duplicate")
        self.assertEqual(username_error.code, "blank")

    def test_cross_field_validation(self):
        """Test cross-field validation errors."""
        data = {
            "email": "test@example.com",
            "age": 25,
            "password": "password123",
            "username": "test@example.com",  # Same as email
        }

        serializer = TestValidationSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        drf_error = ValidationError(serializer.errors)
        standard_exc = convert_drf_validation_error(drf_error)

        # Should have username error
        username_error = next(e for e in standard_exc.errors if e.attr == "username")
        self.assertIn("same", username_error.detail.lower())


class BusinessLogicValidationTestCase(TestCase):
    """Test business logic validation errors."""

    def test_forbidden_content_error(self):
        """Test business rule validation for forbidden content."""
        data = {
            "title": "This is spam content",  # Contains forbidden word
            "content": "Some content here",
            "is_published": False,
        }

        serializer = TestBusinessLogicSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        drf_error = ValidationError(serializer.errors)
        standard_exc = convert_drf_validation_error(drf_error)

        title_error = next(e for e in standard_exc.errors if e.attr == "title")
        self.assertEqual(title_error.code, "forbidden_content")
        self.assertIn("forbidden", title_error.detail.lower())

    def test_business_logic_cross_field_validation(self):
        """Test business logic cross-field validation."""
        data = {
            "title": "Good title",
            "content": "Short",  # Too short for published post
            "is_published": True,
        }

        serializer = TestBusinessLogicSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        drf_error = ValidationError(serializer.errors)
        standard_exc = convert_drf_validation_error(drf_error)

        # Should have errors for both content and is_published
        content_error = next(e for e in standard_exc.errors if e.attr == "content")
        published_error = next(
            e for e in standard_exc.errors if e.attr == "is_published"
        )

        self.assertIn("50 characters", content_error.detail)
        self.assertIn("insufficient", published_error.detail.lower())


class ExceptionHandlerResponseTestCase(TestCase):
    """Test that exception handler returns proper 422 responses."""

    def test_validation_error_returns_422(self):
        """Test that ValidationError returns 422 status."""
        exc = ValidationError({"email": ["This field is required."]})
        context = {"view": None, "request": None}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_complex_validation_error_structure(self):
        """Test complex validation error structure."""
        exc = ValidationError(
            {
                "email": ["This field is required.", "Invalid email format."],
                "password": ["This field must be at least 8 characters."],
                "non_field_errors": ["Username and email cannot be the same."],
            }
        )
        context = {"view": None, "request": None}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

        import json

        data = json.loads(response.content)

        # Check standard format
        self.assertIn("message", data)
        self.assertIn("errors", data)
        self.assertIsInstance(data["errors"], list)
        self.assertTrue(len(data["errors"]) >= 3)  # At least 3 errors

        # Check that each error has required fields
        for error in data["errors"]:
            self.assertIn("code", error)
            self.assertIn("detail", error)
            # attr is optional

        # Check specific errors
        email_errors = [e for e in data["errors"] if e.get("attr") == "email"]
        self.assertEqual(len(email_errors), 2)

        password_errors = [e for e in data["errors"] if e.get("attr") == "password"]
        self.assertEqual(len(password_errors), 1)

        non_field_errors = [e for e in data["errors"] if e.get("attr") is None]
        self.assertTrue(len(non_field_errors) >= 1)


class ErrorFormatConsistencyTestCase(TestCase):
    """Test that all error responses follow the same format."""

    def test_error_format_has_required_fields(self):
        """Test that error format always has required fields."""
        test_cases = [
            ValidationError({"email": ["Required field."]}),
            ValidationError(["General error."]),
            ValidationError("Single string error."),
        ]

        context = {"view": None, "request": None}

        for exc in test_cases:
            with self.subTest(exc=exc):
                response = custom_exception_handler(exc, context)

                import json

                data = json.loads(response.content)

                # Required fields
                self.assertIn("message", data)
                self.assertIn("errors", data)

                # Message must be string
                self.assertIsInstance(data["message"], str)
                self.assertTrue(len(data["message"]) > 0)

                # Errors must be list
                self.assertIsInstance(data["errors"], list)
                self.assertTrue(len(data["errors"]) > 0)

                # Each error must have required fields
                for error in data["errors"]:
                    self.assertIn("code", error)
                    self.assertIn("detail", error)

                    self.assertIsInstance(error["code"], str)
                    self.assertIsInstance(error["detail"], str)

                    # attr is optional but if present, must be string or None
                    if "attr" in error:
                        self.assertTrue(
                            error["attr"] is None or isinstance(error["attr"], str)
                        )
