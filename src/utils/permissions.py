from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from loguru import logger

from apps.common.constants import GroupPermission


def create_group(group_name: str) -> Group:
    group, created = Group.objects.get_or_create(name=group_name)
    if created:
        logger.info(f"Group '{group_name}' created.")
    else:
        logger.info(f"Group '{group_name}' already exists.")

    return group


def create_permission(permission_name: str, content_type: ContentType) -> Permission:
    permission, created = Permission.objects.get_or_create(
        codename=permission_name,
        content_type=content_type,
        defaults={
            "name": f"Can {permission_name.replace('_', ' ')}",
        },
    )

    if created:
        logger.info(f"Permission '{permission_name}' created.")
    else:
        logger.info(f"Permission '{permission_name}' already exists.")

    return permission


def create_groups_and_permissions(
    group_config: GroupPermission, content_type: ContentType
):
    for group_name, permissions in group_config.items():
        group = create_group(group_name)
        for permission_name in permissions:
            permission = create_permission(permission_name, content_type)
            group.permissions.add(permission)

        group.save()
