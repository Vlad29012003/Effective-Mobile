import logging

from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone


@receiver(user_logged_in)
def expire_other_sessions(sender, request, user, **kwargs):
    """
    Signal handler for user logged in event. Expire all other sessions of the user except the current one.
    """
    qs = Session.objects.filter(expire_date__gte=timezone.now())

    for sess in qs:
        data = sess.get_decoded()
        if (
            data.get("_auth_user_id") == str(user.id)
            and sess.session_key != request.session.session_key
        ):
            sess.expire_date = timezone.now()
            sess.save()


@receiver(user_login_failed)
def block_user(sender, request, credentials, **kwargs):
    """
    Signal handler for user login failed event. If login failed 3 times, make user is_active False
    """
    user = User.objects.filter(username=credentials.get("username")).first()

    if user and user.is_active:
        cache.get_or_set(
            f"login_failed_{user.id}",
            0,
            timeout=60,
        )

        cache.incr(f"login_failed_{user.id}")

        if int(cache.get(f"login_failed_{user.id}")) >= 3:
            logging.warning(
                "User {id}.{username} failed to login 3 times, deactivating account",
                extra={
                    "id": user.id,
                    "username": user.username,
                },
            )

            user.is_active = False
            user.save()


@receiver(post_migrate)
def create_groups(sender, **kwargs):
    pass
