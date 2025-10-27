from .base import *

# Logify
LOGGING = get_logging_config(level="INFO", json_logs=True)

# Sentry
SENTRY_DSN = config("SENTRY_DSN")

if not IS_TESTING:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    SENTRY_ENVIRONMENT = config("SENTRY_ENVIRONMENT")
    SENTRY_RELEASE = config("SENTRY_RELEASE")

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.01,
        send_default_pii=True,
        environment=SENTRY_ENVIRONMENT,
        release=SENTRY_RELEASE,
    )
