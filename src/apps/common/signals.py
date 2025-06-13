from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from loguru import logger

# from apps.ov_banks.constants import BANK_GROUP_CONFIG, PSP_GROUP_CONFIG
# from apps.ov_transactions.constants import (
#     TRANSACTION_GROUP_CONFIG,
#     TRANSACTION_TYPE_CONFIG,
#     TransactionActions,
# )
from utils.permissions import create_groups_and_permissions


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
            logger.warning(
                "User {id}.{username} failed to login 3 times, deactivating account",
                id=user.id,
                username=user.username,
            )

            user.is_active = False
            user.save()


@receiver(post_migrate)
def create_groups(sender, **kwargs):
    pass
    # ov_banks_app = "ov_banks"
    # ov_transactions_app = "ov_transactions"

    # bank_content_type = ContentType.objects.filter(
    #     app_label=ov_banks_app, model="bank"
    # ).first()
    # psp_content_type = ContentType.objects.filter(
    #     app_label=ov_banks_app, model="psp"
    # ).first()
    # transaction_content_type = ContentType.objects.filter(
    #     app_label=ov_transactions_app, model="transaction"
    # ).first()
    # transaction_type_content_type = ContentType.objects.filter(
    #     app_label=ov_transactions_app, model="transactiontype"  # noqa
    # ).first()

    # if bank_content_type:
    #     create_groups_and_permissions(BANK_GROUP_CONFIG, bank_content_type)
    #
    # if psp_content_type:
    #     create_groups_and_permissions(PSP_GROUP_CONFIG, psp_content_type)
    #
    # if transaction_content_type:
    #     create_groups_and_permissions(
    #         TRANSACTION_GROUP_CONFIG, transaction_content_type
    #     )
    #
    # if transaction_type_content_type:
    #     create_groups_and_permissions(
    #         TRANSACTION_TYPE_CONFIG, transaction_type_content_type
    #     )
