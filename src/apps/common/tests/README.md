# Error Handling Tests

This directory contains comprehensive tests for the company standard error handling implementation.

## Test Files

### `test_error_handling.py`
- Tests for basic error classes (`StandardError`, `StandardAPIException`)
- Tests for exception conversion (`convert_drf_validation_error`)
- Tests for error codes constants
- Basic API integration tests

### `test_validation_errors.py`
- Detailed validation error testing using test serializers
- Tests for various validation scenarios (required fields, format errors, business logic)
- Tests for 422 response format consistency

### `test_api_error_integration.py`
- Integration tests with actual API endpoints
- Tests for different HTTP status codes (401, 403, 404, 422, etc.)
- Real-world error scenario testing

### `test_error_serializers.py`
- Test serializers specifically designed to trigger validation errors
- Includes business logic validation examples

### `test_runner.py`
- Test suite runner for all error handling tests
- Utility functions for running tests programmatically

## Running Tests

### Run All Error Handling Tests
```bash
python manage.py test tests.test_error_handling tests.test_validation_errors tests.test_api_error_integration
```

### Run Specific Test File
```bash
python manage.py test tests.test_error_handling
```

### Run Specific Test Case
```bash
python manage.py test tests.test_error_handling.StandardErrorTestCase
```

### Run Specific Test Method
```bash
python manage.py test tests.test_error_handling.StandardErrorTestCase.test_standard_error_creation
```

### Run with Verbosity
```bash
python manage.py test tests.test_error_handling -v 2
```

## What These Tests Verify

### ✅ Standard Error Format
- All errors follow the company standard format:
  ```json
  {
    "message": "Validation failed",
    "errors": [
      {
        "code": "required",
        "detail": "This field is required.",
        "attr": "email"
      }
    ]
  }
  ```

### ✅ HTTP Status Code Standards
- ValidationError (DRF) → **422** (Unprocessable Entity) instead of 400
- PermissionDenied → **403** (Forbidden) with standard format
- NotFound → **404** (Not Found) with standard format
- AuthenticationFailed → **401** (Unauthorized) with standard format

### ✅ Error Code Consistency
- All errors have consistent error codes from `ErrorCodes` constants
- Custom validation errors preserve their codes
- Business logic errors have appropriate codes

### ✅ Exception Handler Integration
- DRF exceptions are automatically converted to standard format
- Custom exceptions work correctly
- No try/except needed in views - handler does everything

### ✅ Field-Level and Cross-Field Validation
- Individual field errors have proper `attr` field
- Cross-field validation errors are properly formatted
- Multiple errors per field are handled correctly

## Test Coverage

The tests cover:
- ✅ Standard error class functionality
- ✅ Exception class hierarchy
- ✅ DRF ValidationError conversion
- ✅ Custom exception handler behavior
- ✅ Serializer validation scenarios
- ✅ API endpoint integration
- ✅ Error format consistency
- ✅ Real-world error scenarios

## Adding New Tests

When adding new error handling features:

1. **Add unit tests** in `test_error_handling.py` for new exception classes
2. **Add serializer tests** in `test_validation_errors.py` for new validation logic
3. **Add integration tests** in `test_api_error_integration.py` for API behavior
4. **Update constants** if adding new error codes to `ErrorCodes`

## Example Test Cases

### Testing Custom Validation
```python
def test_custom_business_rule(self):
    """Test custom business rule validation."""
    data = {'title': 'forbidden content'}
    serializer = MySerializer(data=data)

    self.assertFalse(serializer.is_valid())

    # Convert to standard format
    drf_error = ValidationError(serializer.errors)
    standard_exc = convert_drf_validation_error(drf_error)

    # Verify standard format
    self.assertEqual(standard_exc.errors[0].code, 'forbidden_content')
```

### Testing API Response
```python
def test_api_validation_response(self):
    """Test API returns 422 with standard format."""
    response = self.client.post('/api/endpoint/', {})

    self.assertEqual(response.status_code, 422)
    self.assertIn('message', response.data)
    self.assertIn('errors', response.data)
```

## Troubleshooting Tests

### Common Issues

1. **Import Errors**: Make sure all test modules are in the Python path
2. **Database Issues**: Tests use Django's test database - ensure proper setup
3. **URL Configuration**: Integration tests may need URL configuration setup
4. **Authentication**: Some tests require user authentication setup

### Debug Tips

- Use `python manage.py test --debug-mode` for detailed error output
- Add `import pdb; pdb.set_trace()` for debugging specific test cases
- Check test database setup with `python manage.py test --keepdb`
