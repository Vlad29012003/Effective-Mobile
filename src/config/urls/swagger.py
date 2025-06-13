from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

swagger_urlpatterns = [
    path("", SpectacularAPIView.as_view(api_version="public"), name="schema-public"),
    path(
        "swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema-public"),
        name="swagger-ui-public",
    ),
    path(
        "redoc/",
        SpectacularRedocView.as_view(url_name="schema-public"),
        name="redoc-public",
    ),
]
