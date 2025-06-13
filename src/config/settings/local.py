from .base import *  # isort: skip

DEBUG = True

DATABASES["default"] = {
    "ENGINE": "django_prometheus.db.backends.sqlite3",
    "NAME": BASE_DIR / "db.sqlite3",
}

LOGGING["loggers"] = {
    "django.db.backends": {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    },
}

SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

CORS_ALLOW_ALL_ORIGINS = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "http")
