from apps.accounts.models.user import User
from apps.common.exceptions import BusinessLogicException, ValidationException


def update_user_profile(user: User,first_name: str | None = None,last_name: str | None = None,middle_name: str | None = None,email: str | None = None,) -> User:
    update_fields = []
    has_changes = False

    if email and email != user.email:
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            raise ValidationException(
                message="Email уже занят",
                errors=[{"code": "email_exists", "detail": "Email уже занят", "attr": "email"}],
            )
        user.email = email
        update_fields.append("email")
        has_changes = True

    if first_name is not None and first_name != user.first_name:
        user.first_name = first_name
        update_fields.append("first_name")
        has_changes = True

    if last_name is not None and last_name != user.last_name:
        user.last_name = last_name
        update_fields.append("last_name")
        has_changes = True

    if middle_name is not None and middle_name != user.middle_name:
        user.middle_name = middle_name
        update_fields.append("middle_name")
        has_changes = True

    if has_changes:
        update_fields.append("updated_at")
        user.save(update_fields=update_fields)

    return user


def soft_delete_user(user: User) -> User:
    if user.is_deleted:
        raise BusinessLogicException(
            message="Пользователь уже удален",
            errors=[{"code": "already_deleted", "detail": "Пользователь уже удален"}],
        )

    user.soft_delete()

    return user

