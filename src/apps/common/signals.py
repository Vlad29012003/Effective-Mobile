import logging

from django.apps import apps
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone

from .groups import GROUP_PERMISSIONS_MATRIX

logger = logging.getLogger(__name__)


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


def create_permissions_from_app_config(sender, **kwargs):
    """Создает разрешения из конфигурации приложений"""
    try:
        # Получаем все приложения
        for app_config in apps.get_app_configs():
            try:
                # Импортируем модуль permissions
                permissions_module = __import__(
                    f"{app_config.name}.permissions", fromlist=["PERMISSIONS"]
                )

                # Проверяем, есть ли PERMISSIONS в модуле
                if hasattr(permissions_module, "PERMISSIONS"):
                    permissions_list = getattr(permissions_module, "PERMISSIONS")
                    create_permissions_for_app(app_config.name, permissions_list)

            except ImportError:
                continue  # Пропускаем приложения без permissions.py

    except Exception as e:
        logger.error(f"Error creating permissions: {e}")


def create_permissions_for_app(app_name, permissions_list):
    """Создает разрешения для конкретного приложения"""
    try:
        app_label = app_name.split(".")[-1]

        # Создаем общий content type для разрешений (можно создать фиктивный)
        content_type, _ = ContentType.objects.get_or_create(
            app_label=app_label, model="permission"
        )

        created_permissions = []
        for codename, name in permissions_list:
            perm, was_created = Permission.objects.get_or_create(
                codename=codename, content_type=content_type, defaults={"name": name}
            )
            if was_created:
                created_permissions.append(codename)
                logger.info(f"Created permission: {codename} for app {app_label}")

        if created_permissions:
            logger.info(
                f"Created {len(created_permissions)} permissions for {app_label}"
            )

    except Exception as e:
        logger.error(f"Error creating permissions for app {app_name}: {e}")


def create_groups_and_assign_permissions():
    """Создает группы и назначает им разрешения"""
    try:
        for group_name, permission_codes in GROUP_PERMISSIONS_MATRIX.items():
            # Создаем группу
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                logger.info(f"Created group: {group_name}")

            # Получаем разрешения по их кодам
            permissions = []
            for perm_code in permission_codes:
                # Извлекаем app_label и codename из full permission
                if "." in perm_code:
                    app_label, codename = perm_code.split(".", 1)
                else:
                    # Если нет префикса, пробуем найти по codename
                    codename = perm_code
                    app_label = None

                try:
                    if app_label:
                        # Пытаемся найти разрешение по app_label
                        content_type = ContentType.objects.get(
                            app_label=app_label, model="permission"
                        )
                        perm = Permission.objects.get(
                            codename=codename, content_type=content_type
                        )
                    else:
                        # Ищем по codename во всех разрешениях
                        perm = Permission.objects.get(codename=codename)

                    permissions.append(perm)
                except Permission.DoesNotExist:
                    logger.warning(
                        f"Permission {perm_code} not found for group {group_name}"
                    )
                except ContentType.DoesNotExist:
                    logger.warning(f"ContentType for {app_label} not found")

            # Назначаем разрешения группе
            if permissions:
                group.permissions.set(permissions)
                logger.info(
                    f"Assigned {len(permissions)} permissions to group {group_name}"
                )

    except Exception as e:
        logger.error(f"Error creating groups: {e}")


@receiver(post_migrate)
def create_app_permissions_and_groups(sender, **kwargs):
    """Сигнал для создания разрешений и групп после миграций"""
    create_permissions_from_app_config(sender, **kwargs)
    create_groups_and_assign_permissions()
