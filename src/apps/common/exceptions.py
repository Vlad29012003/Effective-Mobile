"""
Standardized error handling following company standards.

Uses 422 (Unprocessable Entity) instead of 400 (Bad Request) for validation errors.
"""

from typing import Any

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError


class StandardError:
    """Single error following company standard format."""

    def __init__(self, code: str, detail: str, attr: str | None = None):
        self.code = code
        self.detail = detail
        self.attr = attr

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        error_dict = {
            "code": self.code,
            "detail": self.detail,
        }
        if self.attr:
            error_dict["attr"] = self.attr
        return error_dict


class StandardAPIException(APIException):
    """Base exception class following company standards."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = _("Validation failed")
    default_code = "validation_failed"

    def __init__(
        self,
        message: str | None = None,
        errors: list[StandardError] | None = None,
        status_code: int | None = None,
    ):
        self.message = message or str(self.default_detail)
        self.errors = errors or []

        if status_code:
            self.status_code = status_code

        # Create detail in DRF expected format
        detail = {
            "message": self.message,
            "errors": [error.to_dict() for error in self.errors],
        }
        super().__init__(detail)


class ValidationException(StandardAPIException):
    """422 Unprocessable Entity for validation errors."""

    default_detail = _("Validation failed")
    default_code = "validation_failed"


class BusinessLogicException(StandardAPIException):
    """422 Unprocessable Entity for business logic violations."""

    default_detail = _("Business logic violation")
    default_code = "business_logic_error"


class ResourceNotFoundException(StandardAPIException):
    """404 Not Found for missing resources."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Resource not found")
    default_code = "not_found"


class PermissionDeniedException(StandardAPIException):
    """403 Forbidden for permission errors."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("Permission denied")
    default_code = "permission_denied"


class ConflictException(StandardAPIException):
    """409 Conflict for resource conflicts."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = _("Resource conflict")
    default_code = "conflict"


def convert_drf_validation_error(
    validation_error: ValidationError,
) -> StandardAPIException:
    """Convert DRF ValidationError to our standard format."""
    errors = []

    if isinstance(validation_error.detail, dict):
        for field, field_errors in validation_error.detail.items():
            if isinstance(field_errors, list):
                for error in field_errors:
                    errors.append(
                        StandardError(
                            code=getattr(error, "code", "invalid"),
                            detail=str(error),
                            attr=field if field != "non_field_errors" else None,
                        )
                    )
            else:
                errors.append(
                    StandardError(
                        code=getattr(field_errors, "code", "invalid"),
                        detail=str(field_errors),
                        attr=field if field != "non_field_errors" else None,
                    )
                )
    elif isinstance(validation_error.detail, list):
        for error in validation_error.detail:
            errors.append(StandardError(code=getattr(error, "code", "invalid"), detail=str(error)))
    else:
        errors.append(
            StandardError(
                code=getattr(validation_error.detail, "code", "invalid"),
                detail=str(validation_error.detail),
            )
        )

    return ValidationException(errors=errors)


# Common error codes constants
class ErrorCodes:
    """Standard error codes for consistency."""

    # Validation errors
    REQUIRED = "required"
    INVALID = "invalid"
    BLANK = "blank"
    NULL = "null"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"

    # Business logic errors
    DUPLICATE = "duplicate"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    CONFLICT = "conflict"
    EXPIRED = "expired"
    LIMIT_EXCEEDED = "limit_exceeded"

    # Authentication errors
    INVALID_CREDENTIALS = "invalid_credentials"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
