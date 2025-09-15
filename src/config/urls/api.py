from django.urls import include, path

from config.urls.auth import auth_urlpatterns
from config.urls.swagger import swagger_urlpatterns

api_urlpatterns = [
    path("accounts/", include("apps.accounts.urls")),
    path("schema/", include(swagger_urlpatterns)),
    path("token/", include(auth_urlpatterns)),
    path("blog/", include("apps.blog.urls")),
]
