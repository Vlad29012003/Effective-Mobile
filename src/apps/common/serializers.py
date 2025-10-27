"""
Serializers for common application.
"""

from rest_framework import serializers


class DependencyCheckSerializer(serializers.Serializer):
    """
    Serializer for individual dependency check result.
    """

    status = serializers.BooleanField(help_text="Dependency status (True if healthy)")
    message = serializers.CharField(help_text="Status message")


class HealthCheckResponseSerializer(serializers.Serializer):
    """
    Serializer for health check response.
    """

    status = serializers.CharField(help_text="Overall application status (healthy/unhealthy)")
    service = serializers.CharField(help_text="Service name")
    timestamp = serializers.IntegerField(help_text="Unix timestamp of the check")
    response_time_ms = serializers.FloatField(help_text="Response time in milliseconds")
    checks = serializers.DictField(child=DependencyCheckSerializer(), help_text="Individual dependency checks")
