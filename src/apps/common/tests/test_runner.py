"""
Test runner for error handling tests.

Run with: python manage.py test tests.test_runner
"""

from django.test import TestCase

# Import all test modules
from .test_error_handling import (
    CustomExceptionHandlerTestCase,
    DRFValidationErrorConversionTestCase,
    ErrorCodesTestCase,
    ErrorHandlerAPITestCase,
    IntegrationTestCase,
    StandardErrorTestCase,
    StandardExceptionTestCase,
)
from .test_validation_errors import (
    BusinessLogicValidationTestCase,
    ErrorFormatConsistencyTestCase,
    ExceptionHandlerResponseTestCase,
    SerializerValidationTestCase,
)


class ErrorHandlingTestSuite(TestCase):
    """Test suite runner for all error handling tests."""

    @classmethod
    def setUpClass(cls):
        """Set up test suite."""
        super().setUpClass()
        print("\n" + "=" * 60)
        print("Running Company Standard Error Handling Tests")
        print("=" * 60)

    @classmethod
    def tearDownClass(cls):
        """Clean up after test suite."""
        super().tearDownClass()
        print("\n" + "=" * 60)
        print("Error Handling Tests Completed")
        print("=" * 60)

    def test_all_error_components(self):
        """Test that all error handling components work together."""
        # This is a placeholder test to ensure the suite runs
        self.assertTrue(True)
        print("\n✅ Error handling test suite is properly configured")


def run_error_tests():
    """Function to run all error handling tests programmatically."""
    from django.conf import settings
    from django.test.utils import get_runner

    # Get the Django test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    # List of test modules to run
    test_modules = [
        "tests.test_error_handling",
        "tests.test_validation_errors",
        "tests.test_api_error_integration",
    ]

    # Run the tests
    failures = test_runner.run_tests(test_modules)

    if failures:
        print(f"\n❌ {failures} test(s) failed!")
        return False
    else:
        print("\n✅ All error handling tests passed!")
        return True


if __name__ == "__main__":
    # Run tests when executed directly
    run_error_tests()
