
import logging

from django.db import connections
from django.http import JsonResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.views import APIView

from .serializers import HealthCheckResponseSerializer

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    permission_classes: list = []

    @extend_schema(
        tags=["health"],
        summary="Application health check",
        description="Returns application status and dependencies check",
        responses={200: HealthCheckResponseSerializer},
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
        detailed = request.GET.get("detailed", "false").lower() == "true"

        if not detailed:
            return JsonResponse({"status": "healthy", "service": "effective-mobile"}, status=200)

        checks = {}
        overall_status = "healthy"

        checks["database"] = self._check_database()

        for _, check_result in checks.items():
            if not check_result["status"]:
                overall_status = "unhealthy"
                break

        return JsonResponse(
            {
                "status": overall_status,
                "service": "effective-mobile",
                "checks": checks,
            },
            status=200 if overall_status == "healthy" else 503,
        )

    def _check_database(self):
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
