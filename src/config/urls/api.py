from django.urls import include, path

from config.urls.swagger import swagger_urlpatterns

api_urlpatterns = [
    path("schema/", include(swagger_urlpatterns)),
]
