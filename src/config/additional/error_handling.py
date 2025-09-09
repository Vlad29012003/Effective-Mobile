"""
Middleware for standardized error handling.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAcceptable,
    NotFound,
    PermissionDenied,
    Throttled,
    UnsupportedMediaType,
    ValidationError,
)
from rest_framework.views import exception_handler

from apps.common.exceptions import (
    ErrorCodes,
    PermissionDeniedException,
    ResourceNotFoundException,
    StandardAPIException,
    StandardError,
    ValidationException,
    convert_drf_validation_error,
)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that converts all DRF exceptions to standard format.

    This handler automatically converts:
    - ValidationError (400) -> 422 with standard format
    - PermissionDenied (403) -> 403 with standard format
    - NotFound (404) -> 404 with standard format
    - Other common DRF exceptions to standard format
    """

    # Handle DRF ValidationError -> 422
    if isinstance(exc, ValidationError):
        return _handle_validation_error(exc)

    # Handle DRF PermissionDenied -> 403
    if isinstance(exc, PermissionDenied):
        return _handle_permission_denied(exc)

    # Handle DRF NotFound -> 404
    if isinstance(exc, NotFound):
        return _handle_not_found(exc)

    # Handle Authentication errors -> 401
    if isinstance(exc, AuthenticationFailed):
        return _handle_authentication_failed(exc)

    # Handle Method Not Allowed -> 405
    if isinstance(exc, MethodNotAllowed):
        return _handle_method_not_allowed(exc)

    # Handle Throttling -> 429
    if isinstance(exc, Throttled):
        return _handle_throttled(exc)

    # Handle Django ValidationError from models/forms
    if isinstance(exc, DjangoValidationError):
        return _handle_django_validation_error(exc)

    # Handle our custom exceptions
    if isinstance(exc, StandardAPIException):
        return _handle_standard_exception(exc)

    # Use DRF's default handler for other exceptions
    response = exception_handler(exc, context)

    # Convert any remaining response to standard format if possible
    if response is not None and hasattr(response, "data"):
        response.data = _ensure_standard_format(response.data, response.status_code)

    return response


def _handle_validation_error(exc):
    """Convert DRF ValidationError to 422 standard format."""
    standard_exc = convert_drf_validation_error(exc)
    return JsonResponse(
        {
            "message": standard_exc.message,
            "errors": [error.to_dict() for error in standard_exc.errors],
        },
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def _handle_permission_denied(exc):
    """Convert PermissionDenied to standard format."""
    return JsonResponse(
        {
            "message": "Permission denied",
            "errors": [
                StandardError(
                    code=ErrorCodes.PERMISSION_DENIED,
                    detail=(
                        str(exc.detail)
                        if hasattr(exc, "detail")
                        else "You do not have permission to perform this action."
                    ),
                ).to_dict()
            ],
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _handle_not_found(exc):
    """Convert NotFound to standard format."""
    return JsonResponse(
        {
            "message": "Resource not found",
            "errors": [
                StandardError(
                    code=ErrorCodes.NOT_FOUND,
                    detail=(
                        str(exc.detail)
                        if hasattr(exc, "detail")
                        else "The requested resource was not found."
                    ),
                ).to_dict()
            ],
        },
        status=status.HTTP_404_NOT_FOUND,
    )


def _handle_authentication_failed(exc):
    """Convert AuthenticationFailed to standard format."""
    return JsonResponse(
        {
            "message": "Authentication failed",
            "errors": [
                StandardError(
                    code=ErrorCodes.INVALID_CREDENTIALS,
                    detail=(
                        str(exc.detail)
                        if hasattr(exc, "detail")
                        else "Invalid authentication credentials."
                    ),
                ).to_dict()
            ],
        },
        status=status.HTTP_401_UNAUTHORIZED,
    )


def _handle_method_not_allowed(exc):
    """Convert MethodNotAllowed to standard format."""
    return JsonResponse(
        {
            "message": "Method not allowed",
            "errors": [
                StandardError(
                    code="method_not_allowed",
                    detail=(
                        str(exc.detail)
                        if hasattr(exc, "detail")
                        else "This HTTP method is not allowed for this endpoint."
                    ),
                ).to_dict()
            ],
        },
        status=status.HTTP_405_METHOD_NOT_ALLOWED,
    )


def _handle_throttled(exc):
    """Convert Throttled to standard format."""
    return JsonResponse(
        {
            "message": "Request throttled",
            "errors": [
                StandardError(
                    code=ErrorCodes.LIMIT_EXCEEDED,
                    detail=(
                        str(exc.detail)
                        if hasattr(exc, "detail")
                        else "Request was throttled. Please try again later."
                    ),
                ).to_dict()
            ],
        },
        status=status.HTTP_429_TOO_MANY_REQUESTS,
    )


def _handle_django_validation_error(exc):
    """Convert Django ValidationError to standard format."""
    errors = []

    if hasattr(exc, "error_dict"):
        # Field-specific errors
        for field, field_errors in exc.error_dict.items():
            for error in field_errors:
                errors.append(
                    StandardError(
                        code=(
                            error.code if hasattr(error, "code") else ErrorCodes.INVALID
                        ),
                        detail=str(
                            error.message if hasattr(error, "message") else error
                        ),
                        attr=field,
                    ).to_dict()
                )
    else:
        # General errors
        for error in exc.error_list:
            errors.append(
                StandardError(
                    code=error.code if hasattr(error, "code") else ErrorCodes.INVALID,
                    detail=str(error.message if hasattr(error, "message") else error),
                ).to_dict()
            )

    return JsonResponse(
        {"message": "Validation failed", "errors": errors},
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def _handle_standard_exception(exc):
    """Handle our custom StandardAPIException."""
    return JsonResponse(
        {"message": exc.message, "errors": [error.to_dict() for error in exc.errors]},
        status=exc.status_code,
    )


def _ensure_standard_format(data, status_code):
    """Ensure response data follows standard format."""
    if isinstance(data, dict) and ("message" in data or "errors" in data):
        return data  # Already in standard format

    # Convert non-standard format to standard
    if isinstance(data, dict):
        detail = data.get("detail", str(data))
    else:
        detail = str(data)

    return {
        "message": _get_default_message_for_status(status_code),
        "errors": [
            StandardError(
                code=_get_default_code_for_status(status_code), detail=detail
            ).to_dict()
        ],
    }


def _get_default_message_for_status(status_code):
    """Get default message for HTTP status code."""
    messages = {
        400: "Bad request",
        401: "Authentication required",
        403: "Permission denied",
        404: "Resource not found",
        405: "Method not allowed",
        422: "Validation failed",
        429: "Too many requests",
        500: "Internal server error",
    }
    return messages.get(status_code, "An error occurred")


def _get_default_code_for_status(status_code):
    """Get default error code for HTTP status code."""
    codes = {
        400: "bad_request",
        401: ErrorCodes.INVALID_CREDENTIALS,
        403: ErrorCodes.PERMISSION_DENIED,
        404: ErrorCodes.NOT_FOUND,
        405: "method_not_allowed",
        422: ErrorCodes.INVALID,
        429: ErrorCodes.LIMIT_EXCEEDED,
        500: "server_error",
    }
    return codes.get(status_code, "error")
