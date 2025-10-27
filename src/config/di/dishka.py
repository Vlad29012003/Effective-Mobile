from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from dishka import Container, Provider, Scope, from_context
from dishka.integrations.base import wrap_injection
from django.conf import settings
from rest_framework.request import Request

T = TypeVar("T")
P = ParamSpec("P")

__all__ = [
    "DRFProvider",
    "inject",
    "setup_dishka",
]


def inject(func: Callable[P, T]) -> Callable[P, T]:  # noqa: UP047
    def get_container(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        request = args[0].request if args and hasattr(args[0], "request") else None

        if not hasattr(request, "dishka_container"):
            raise RuntimeError("Container not found in request. Make sure DishkaMiddleware is properly configured.")

        return request.dishka_container  # type: ignore

    return wrap_injection(
        func=func,
        container_getter=get_container,
    )


class DRFProvider(Provider):
    """
    Provider for Django Rest Framework.
    """

    request = from_context(Request, scope=Scope.REQUEST)
    user = from_context("request.user", scope=Scope.REQUEST)


def setup_dishka(container: Container) -> None:
    """
    Initialize Dishka with DRF application.
    Must be called before running the application.
    """
    if not hasattr(settings, "MIDDLEWARE"):
        settings.MIDDLEWARE = []

    middleware_path = "config.middlewares.dishka.DishkaMiddleware"

    if middleware_path not in settings.MIDDLEWARE:
        settings.MIDDLEWARE.insert(0, middleware_path)

    settings.DISHKA_CONTAINER = container
