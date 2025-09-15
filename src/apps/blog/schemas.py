from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiParameter

from apps.common.schema import BaseViewSchema


class PostPublishActionSchema(BaseViewSchema):
    schema = {
        "methods": ["POST"],
        "summary": _("Publish existing post"),
        "description": _("Publish an existing post"),
        "request": None,
        "parameters": [
            OpenApiParameter(
                name="id",
                description="Post ID",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
    }


class PostUnpublishActionSchema(BaseViewSchema):
    schema = {
        "methods": ["POST"],
        "summary": _("Unpublish post"),
        "description": _(
            "Unpublish a published post, changing its status back to Draft"
        ),
        "request": None,
        "parameters": [
            OpenApiParameter(
                name="id",
                description="Post ID",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
    }
