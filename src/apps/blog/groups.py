"""
Конфигурация групп пользователей и их разрешений для блога.
"""

from .permissions import BlogPermission

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
