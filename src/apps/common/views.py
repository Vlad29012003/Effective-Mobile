"""
Common views for health checks and error testing.
"""

import logging

import boto3
from botocore.exceptions import ClientError
from celery import Celery
from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.http import JsonResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.views import APIView

from .serializers import HealthCheckResponseSerializer

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Health check endpoint for application monitoring.
    """

    permission_classes: list = []

    @extend_schema(
        tags=["health"],
        summary="Application health check",
        description="Returns application status and dependencies check",
        responses={200: HealthCheckResponseSerializer},
        # Parameters detail True, False
        parameters=[
            OpenApiParameter(
                name="detailed",
                type=bool,
                description="If true, returns detailed status of each dependency",
                required=False,
            )
        ],
    )
    def get(self, request):
        """Application health check with dependencies validation."""
        detailed = request.GET.get("detailed", "false").lower() == "true"

        if not detailed:
            return JsonResponse({"status": "healthy", "service": "django-blog-template"}, status=200)

        checks = {}
        overall_status = "healthy"

        checks["database"] = self._check_database()
        checks["redis"] = self._check_redis()
        checks["celery"] = self._check_celery()
        checks["minio"] = self._check_minio()

        for _, check_result in checks.items():
            if not check_result["status"]:
                overall_status = "unhealthy"
                break

        return JsonResponse(
            {
                "status": overall_status,
                "service": "django-blog-template",
                "checks": checks,
            },
            status=200 if overall_status == "healthy" else 503,
        )

    def _check_database(self):
        """Check PostgreSQL database connectivity."""
        try:
            db_conn = connections["default"]
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    return {"status": True, "message": "Database connection successful"}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": False, "message": f"Database connection failed: {str(e)}"}

    def _check_redis(self):
        """Check Redis connectivity."""
        try:
            cache.set("health_check", "test", 10)
            result = cache.get("health_check")
            if result == "test":
                cache.delete("health_check")
                return {"status": True, "message": "Redis connection successful"}
            else:
                return {"status": False, "message": "Redis test failed"}
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": False, "message": f"Redis connection failed: {str(e)}"}

    def _check_celery(self):
        """Check Celery broker connectivity."""
        try:
            celery_app = Celery("health_check")
            celery_app.config_from_object("django.conf:settings", namespace="CELERY")

            inspect = celery_app.control.inspect()
            stats = inspect.stats()

            if stats:
                return {
                    "status": True,
                    "message": "Celery broker connection successful",
                }
            else:
                return {"status": False, "message": "No Celery workers available"}
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {
                "status": False,
                "message": f"Celery broker connection failed: {str(e)}",
            }

    def _check_minio(self):
        """Check MinIO/S3 connectivity."""
        if not getattr(settings, "USE_S3", False):
            return {
                "status": True,
                "message": "MinIO not configured (local storage used)",
            }

        try:
            s3_client = boto3.client(
                "s3",
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

            s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            return {"status": True, "message": "MinIO connection successful"}
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                logger.error(f"MinIO bucket not found: {settings.AWS_STORAGE_BUCKET_NAME}")
                return {
                    "status": False,
                    "message": f"MinIO bucket not found: {settings.AWS_STORAGE_BUCKET_NAME}",
                }
            else:
                logger.error(f"MinIO health check failed: {e}")
                return {
                    "status": False,
                    "message": f"MinIO connection failed: {str(e)}",
                }
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
            return {"status": False, "message": f"MinIO connection failed: {str(e)}"}


def trigger_error(request):
    1 / 0  # noqa: B018
