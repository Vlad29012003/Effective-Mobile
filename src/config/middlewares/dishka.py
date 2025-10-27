from django.conf import settings


class DishkaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.container = getattr(settings, "DISHKA_CONTAINER", None)

        if self.container is None:
            raise ValueError(
                "DISHKA_CONTAINER not found in settings. Please call setup_dishka before running the application."
            )

    def __call__(self, request):
        request.dishka_container = self.container
        response = self.get_response(request)
        return response
