from .base import *  # isort: skip

# Sentry
SENTRY_DSN = config("SENTRY_DSN", default=None)

if SENTRY_DSN and not IS_TESTING:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    SENTRY_ENVIRONMENT = config("SENTRY_ENVIRONMENT")
    SENTRY_RELEASE = config("SENTRY_RELEASE")

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment=SENTRY_ENVIRONMENT,
        release=SENTRY_RELEASE,
    )
