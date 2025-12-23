from django.conf import settings
from django.contrib.auth import get_user_model

User: settings.AUTH_USER_MODEL = get_user_model()
