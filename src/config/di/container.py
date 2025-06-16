from dishka import Provider, Scope, make_container

from apps.blog.services import PostService
from config.di.dishka import DRFProvider, setup_dishka


def setup_container():
    provider = Provider()

    provider.provide(PostService, scope=Scope.APP)

    container = make_container(provider, DRFProvider())

    setup_dishka(container)
