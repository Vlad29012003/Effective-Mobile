from rest_framework import serializers


class DependencyCheckSerializer(serializers.Serializer):
    status = serializers.BooleanField(help_text="Dependency status (True if healthy)")
    message = serializers.CharField(help_text="Status message")


class HealthCheckResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="Overall application status (healthy/unhealthy)")
    service = serializers.CharField(help_text="Service name")
    checks = serializers.DictField(child=DependencyCheckSerializer(), help_text="Individual dependency checks")
