from dishka import Provider, Scope, make_container

from config.di.dishka import DRFProvider, setup_dishka


def setup_container():
    provider = Provider()

    container = make_container(provider, DRFProvider())

    setup_dishka(container)
