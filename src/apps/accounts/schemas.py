from drf_spectacular.openapi import OpenApiExample
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse

from apps.accounts.serializers import PermissionCheckRequestSerializer
from apps.common.schema import BaseViewSchema


class PermissionCheckViewSchema(BaseViewSchema):
    schema = {
        "tags": ["permissions"],
        "summary": "Check multiple permissions",
        "description": "Check multiple permissions for the current user",
        "request": PermissionCheckRequestSerializer,
        "responses": {
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        "Example Response",
                        value={
                            "action": True,
                            "action2": False,
                        },
                        summary="Permission check results",
                    )
                ],
            )
        },
    }
