from apps.accounts.permissions.admin import IsAdmin
from apps.accounts.permissions.base import HasObjectPermission, HasPermission

__all__ = [
    "HasPermission",
    "HasObjectPermission",
    "IsAdmin",
]
