import logging

import boto3
import redis
from django.conf import settings
from django.core.cache import caches
from django.db import connections
from rest_framework.response import Response
from rest_framework.views import APIView

from config.celery import app as celery_app

logger = logging.getLogger(__name__)


def trigger_error(request):
    """
    For sentry health check and testing purposes.
    :param request:
    :return:
    """
    1 / 0


class HealthCheckView(APIView):
    authentication_classes = []  # type: ignore
    permission_classes = []  # type: ignore

    def get(self, request, *args, **kwargs):
        checks = {}

        def safe_check(name, fn):
            try:
                fn()
                checks[name] = "ok"
            except Exception as e:
                logger.error(f"{name} health check failed: {e}", exc_info=True)
                checks[name] = f"error: {str(e)}"

        # DB check(s)
        for alias in [a for a in ["default", "ov_database"] if a in settings.DATABASES]:
            safe_check(
                f"db_{alias}", lambda: connections[alias].cursor().execute("SELECT 1")
            )

        # Redis
        def check_cache():
            cache = caches["default"]
            cache.set("health_check_key", "ok", timeout=5)
            if cache.get("health_check_key") != "ok":
                raise Exception("Redis set/get failed")
            cache.delete("health_check_key")

        safe_check("cache_redis", check_cache)

        # Celery broker
        def check_broker():
            with celery_app.broker_connection(connect_timeout=3) as conn:
                conn.ensure_connection(timeout=3, max_retries=1)

        safe_check("broker_celery", check_broker)

        # S3 / MinIO
        def check_s3():
            boto3.client(
                "s3",
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=getattr(settings, "AWS_S3_REGION_NAME", "us-east-1"),
            ).head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)

        safe_check("storage_s3", check_s3)

        status = "ok" if all(v == "ok" for v in checks.values()) else "error"
        return Response({"status": status, "checks": checks})
