"""
Serializers for common application.
"""

from rest_framework import serializers


class HealthCheckResponseSerializer(serializers.Serializer):
    """
    Serializer for health check response.
    """

    status = serializers.CharField(help_text="Application status")
    service = serializers.CharField(help_text="Service name")
