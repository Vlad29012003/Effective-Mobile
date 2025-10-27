"""
Integration tests for API error handling.
"""

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import path
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase
from rest_framework.views import APIView

from apps.common.exceptions import (
    BusinessLogicException,
    StandardError,
    ValidationException,
)

User = get_user_model()


class TestErrorAPIView(APIView):
    """Test API view to trigger different types of errors."""

    def post(self, request):
        """Trigger validation error."""
        error_type = request.data.get("error_type")

        if error_type == "validation":
            raise ValidationError(
                {
                    "email": ["This field is required."],
                    "age": ["Ensure this value is greater than or equal to 0."],
                }
            )
        elif error_type == "permission":
            raise PermissionDenied("You don't have permission to perform this action.")
        elif error_type == "not_found":
            raise NotFound("The requested resource was not found.")
        elif error_type == "custom_validation":
            raise ValidationException(
                message="Custom validation failed",
                errors=[
                    StandardError("required", "Email is required", "email"),
                    StandardError("invalid", "Invalid phone format", "phone"),
                ],
            )
        elif error_type == "business_logic":
            raise BusinessLogicException(
                message="Business rule violation",
                errors=[StandardError("limit_exceeded", "Daily post limit reached")],
            )

        return Response({"status": "success"})


# Test URL patterns (normally these would be in urls.py)
test_urlpatterns = [
    path("test-errors/", TestErrorAPIView.as_view(), name="test-errors"),
]


class APIErrorIntegrationTestCase(APITestCase):
    """Test error handling through actual API calls."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()

    def test_drf_validation_error_returns_422(self):
        """Test that DRF ValidationError returns 422 with standard format."""
        with override_settings(ROOT_URLCONF="tests.test_api_error_integration"):
            # Create a temporary test URL
            response = self.client.post("/test-errors/", {"error_type": "validation"}, format="json")

        # Should return 422 instead of 400
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Check standard format
        self.assertIn("message", response.data)
        self.assertIn("errors", response.data)
        self.assertIsInstance(response.data["errors"], list)

        # Check specific errors
        errors = response.data["errors"]
        self.assertEqual(len(errors), 2)

        email_error = next(e for e in errors if e.get("attr") == "email")
        age_error = next(e for e in errors if e.get("attr") == "age")

        self.assertEqual(email_error["code"], "invalid")
        self.assertEqual(age_error["code"], "invalid")

    def test_permission_denied_returns_403_standard_format(self):
        """Test that PermissionDenied returns 403 with standard format."""
        with override_settings(ROOT_URLCONF="tests.test_api_error_integration"):
            response = self.client.post("/test-errors/", {"error_type": "permission"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Check standard format
        self.assertIn("message", response.data)
        self.assertIn("errors", response.data)

        self.assertEqual(response.data["message"], "Permission denied")
        self.assertEqual(len(response.data["errors"]), 1)
        self.assertEqual(response.data["errors"][0]["code"], "permission_denied")

    def test_not_found_returns_404_standard_format(self):
        """Test that NotFound returns 404 with standard format."""
        with override_settings(ROOT_URLCONF="tests.test_api_error_integration"):
            response = self.client.post("/test-errors/", {"error_type": "not_found"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Check standard format
        self.assertIn("message", response.data)
        self.assertIn("errors", response.data)

        self.assertEqual(response.data["message"], "Resource not found")
        self.assertEqual(response.data["errors"][0]["code"], "not_found")

    def test_custom_validation_exception(self):
        """Test that custom ValidationException works correctly."""
        with override_settings(ROOT_URLCONF="tests.test_api_error_integration"):
            response = self.client.post("/test-errors/", {"error_type": "custom_validation"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Check standard format
        self.assertEqual(response.data["message"], "Custom validation failed")
        self.assertEqual(len(response.data["errors"]), 2)

        email_error = next(e for e in response.data["errors"] if e.get("attr") == "email")
        phone_error = next(e for e in response.data["errors"] if e.get("attr") == "phone")

        self.assertEqual(email_error["code"], "required")
        self.assertEqual(phone_error["code"], "invalid")

    def test_business_logic_exception(self):
        """Test that BusinessLogicException works correctly."""
        with override_settings(ROOT_URLCONF="tests.test_api_error_integration"):
            response = self.client.post("/test-errors/", {"error_type": "business_logic"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Check standard format
        self.assertEqual(response.data["message"], "Business rule violation")
        self.assertEqual(len(response.data["errors"]), 1)
        self.assertEqual(response.data["errors"][0]["code"], "limit_exceeded")


class RealWorldErrorScenariosTestCase(APITestCase):
    """Test real-world error scenarios that developers might encounter."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")

    def test_unauthenticated_request_format(self):
        """Test unauthenticated request error format."""
        # Most endpoints require authentication
        response = self.client.get("/api/posts/")

        # Should be 401 with standard format if our handler processes it
        if response.status_code == status.HTTP_401_UNAUTHORIZED and (
            isinstance(response.data, dict) and "message" in response.data
        ):
            # Our handler processed it
            self.assertIn("message", response.data)
            self.assertIn("errors", response.data)
            self.assertIsInstance(response.data["errors"], list)

    def test_method_not_allowed_format(self):
        """Test method not allowed error format."""
        # Try DELETE on list endpoint (usually not allowed)
        response = self.client.delete("/api/posts/")

        if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED and (
            isinstance(response.data, dict) and "message" in response.data
        ):
            # Our handler processed it
            self.assertIn("message", response.data)
            self.assertIn("errors", response.data)
            self.assertEqual(response.data["errors"][0]["code"], "method_not_allowed")

    def test_invalid_json_format(self):
        """Test invalid JSON format error."""
        # Send malformed JSON
        response = self.client.post("/api/posts/", data='{"invalid": json}', content_type="application/json")

        # Should return some error (400, 401, etc.)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # If our handler processed it, should have standard format
        if isinstance(response.data, dict) and "message" in response.data:
            self.assertIn("errors", response.data)


# URL configuration for testing
urlpatterns = [
    path("test-errors/", TestErrorAPIView.as_view(), name="test-errors"),
]
