"""
Конфигурация групп пользователей и их разрешений.
"""

from apps.blog.permissions import BlogPermission

# Определение групп и их разрешений
GROUP_PERMISSIONS_MATRIX = {
    "Bloggers": [
        BlogPermission.VIEW_POST.value,
        BlogPermission.CREATE_POST.value,
        BlogPermission.EDIT_POST.value,
        BlogPermission.DELETE_POST.value,
        BlogPermission.PUBLISH_POST.value,
    ],
    "Moderators": [
        BlogPermission.VIEW_POST.value,
        BlogPermission.CREATE_POST.value,
        BlogPermission.EDIT_POST.value,
        BlogPermission.DELETE_POST.value,
        BlogPermission.PUBLISH_POST.value,
        BlogPermission.EDIT_ANY_POST.value,
    ],
    "Editors": [
        BlogPermission.VIEW_POST.value,
        BlogPermission.CREATE_POST.value,
        BlogPermission.EDIT_POST.value,
        BlogPermission.DELETE_POST.value,
        BlogPermission.PUBLISH_POST.value,
        BlogPermission.EDIT_ANY_POST.value,
        BlogPermission.DELETE_ANY_POST.value,
    ],
}
