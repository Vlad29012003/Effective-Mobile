from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models.rbac import Permission, PermissionAction, Role, RolePermission, UserRole

User = get_user_model()


class Command(BaseCommand):
    help = "Создает тестовые данные для демонстрации RBAC системы"

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            type=str,
            default="test123456",
            help="Пароль для тестовых пользователей (по умолчанию: test123456)",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Удалить существующие тестовые данные перед созданием новых",
        )

    def handle(self, *args, **options):
        password = options["password"]
        reset = options["reset"]

        self.stdout.write(self.style.SUCCESS("Начало создания тестовых данных..."))

        with transaction.atomic():
            if reset:
                self._reset_test_data()

            roles = self._create_roles()
            permissions = self._create_permissions()
            self._assign_permissions_to_roles(roles, permissions)
            users = self._create_users(password)
            self._assign_roles_to_users(users, roles)

        self.stdout.write(self.style.SUCCESS("Тестовые данные успешно созданы!"))

    def _reset_test_data(self):
        self.stdout.write("Удаление существующих тестовых данных...")

        test_emails = ["admin@test.com", "user@test.com", "moderator@test.com"]
        User.objects.filter(email__in=test_emails).delete()

        test_role_names = ["admin", "user", "moderator"]
        Role.objects.filter(name__in=test_role_names, is_system=False).delete()

        self.stdout.write(self.style.WARNING("Старые тестовые данные удалены"))

    def _create_roles(self):
        roles_data = [
            {"name": "admin", "description": "Администратор с полными правами", "is_system": True},
            {"name": "user", "description": "Обычный пользователь", "is_system": True},
            {"name": "moderator", "description": "Модератор с правами на редактирование", "is_system": False},
        ]

        roles = {}
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data["name"],
                defaults={
                    "description": role_data["description"],
                    "is_system": role_data["is_system"],
                },
            )
            roles[role_data["name"]] = role
            if created:
                self.stdout.write(f"  ✓ Создана роль: {role.name}")
            else:
                self.stdout.write(f"  - Роль уже существует: {role.name}")

        return roles

    def _create_permissions(self):
        permissions_data = [
            {"code": "blog.post.create", "name": "Создание поста", "resource_type": "blog.post", "action": PermissionAction.CREATE},
            {"code": "blog.post.read", "name": "Чтение поста", "resource_type": "blog.post", "action": PermissionAction.READ},
            {"code": "blog.post.update", "name": "Обновление поста", "resource_type": "blog.post", "action": PermissionAction.UPDATE},
            {"code": "blog.post.delete", "name": "Удаление поста", "resource_type": "blog.post", "action": PermissionAction.DELETE},
            {"code": "blog.post.list", "name": "Список постов", "resource_type": "blog.post", "action": PermissionAction.LIST},
        ]

        permissions = {}
        for perm_data in permissions_data:
            permission, created = Permission.objects.get_or_create(
                code=perm_data["code"],
                defaults={
                    "name": perm_data["name"],
                    "resource_type": perm_data["resource_type"],
                    "action": perm_data["action"],
                },
            )
            permissions[perm_data["code"]] = permission
            if created:
                self.stdout.write(f"  ✓ Создано право: {permission.code}")
            else:
                self.stdout.write(f"  - Право уже существует: {permission.code}")

        return permissions

    def _assign_permissions_to_roles(self, roles, permissions):
        role_permissions_map = {
            "admin": [
                "blog.post.create",
                "blog.post.read",
                "blog.post.update",
                "blog.post.delete",
                "blog.post.list",
            ],
            "user": [
                "blog.post.read",
                "blog.post.list",
            ],
            "moderator": [
                "blog.post.read",
                "blog.post.list",
                "blog.post.update",
                "blog.post.delete",
            ],
        }

        for role_name, permission_codes in role_permissions_map.items():
            role = roles[role_name]
            for perm_code in permission_codes:
                permission = permissions[perm_code]
                role_permission, created = RolePermission.objects.get_or_create(
                    role=role,
                    permission=permission,
                )
                if created:
                    self.stdout.write(f"  ✓ Назначено право {perm_code} роли {role_name}")

    def _create_users(self, password):
        users_data = [
            {"email": "admin@test.com", "first_name": "Admin", "last_name": "User"},
            {"email": "user@test.com", "first_name": "Regular", "last_name": "User"},
            {"email": "moderator@test.com", "first_name": "Moderator", "last_name": "User"},
        ]

        users = {}
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data["email"],
                defaults={
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "is_active": True,
                },
            )
            if created or not user.check_password(password):
                user.set_password(password)
                user.save()
                self.stdout.write(f"  ✓ Создан/обновлен пользователь: {user.email} (пароль: {password})")
            else:
                self.stdout.write(f"  - Пользователь уже существует: {user.email}")

            users[user_data["email"]] = user

        return users

    def _assign_roles_to_users(self, users, roles):
        user_roles_map = {
            "admin@test.com": "admin",
            "user@test.com": "user",
            "moderator@test.com": "moderator",
        }

        for email, role_name in user_roles_map.items():
            user = users[email]
            role = roles[role_name]
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
            )
            if created:
                self.stdout.write(f"  ✓ Назначена роль {role_name} пользователю {email}")
            else:
                self.stdout.write(f"  - Роль {role_name} уже назначена пользователю {email}")

