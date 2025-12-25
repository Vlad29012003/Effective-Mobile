# Effective Mobile - Система аутентификации и авторизации

## Описание

Это тестовое задание, реализующее backend-приложение с собственной системой аутентификации и авторизации. Приложение разработано с использованием следующих технологий:

### Технологический стек

- **Python 3.12+** — язык программирования
- **Django 5.2.3** — веб-фреймворк
- **Django REST Framework** — фреймворк для построения REST API
- **PostgreSQL** — реляционная база данных
- **JWT (JSON Web Tokens)** — аутентификация через токены (djangorestframework-simplejwt)
- **Docker & Docker Compose** — контейнеризация для локальной разработки
- **DRF Spectacular** — автоматическая генерация Swagger/OpenAPI документации
- **Django Unfold** — современный админ-интерфейс

### Основные возможности

- **RBAC (Role-Based Access Control)** — система управления доступом на основе ролей
- **Object-level Permissions** — права доступа на уровне конкретных объектов
- **JWT аутентификация** — безопасная аутентификация через токены с поддержкой blacklist
- **Soft Delete** — мягкое удаление пользователей (сохранение данных в БД)
- **REST API** — полный набор эндпоинтов для управления пользователями и правами доступа
- **Административный API** — управление ролями, правами и их назначением через API

## Установка и запуск проекта

### Требования

- **Python 3.12+** — последняя версия Python
- **Docker & Docker Compose** — для запуска через контейнеры
- **Git** — для клонирования репозитория

### Клонирование репозитория

```bash
git clone https://github.com/Vlad29012003/Effective-Mobile.git
cd Effective-Mobile
```

### Настройка переменных окружения

Создайте файл `.env` в корне проекта (`/effective-mobile/.env`) со следующим содержимым:

```env
DJANGO_SECRET_KEY=your-secret-key-change-me
DEBUG=True
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://*
CSRF_TRUSTED_ORIGINS=http://*

POSTGRES_DB=blog
POSTGRES_USER=admin
POSTGRES_PASSWORD=postgres123
POSTGRES_HOST=db
POSTGRES_PORT=5432
SESSION_AGE=15
```

**Важно:** Измените `DJANGO_SECRET_KEY` на уникальное значение для продакшена.

### Запуск через Docker Compose

Запустите проект с помощью Docker Compose:

```bash
docker compose -f docker-compose-locale.yml up --build
```

Эта команда:
- Соберет Docker-образы
- Запустит контейнеры PostgreSQL и Django
- Автоматически выполнит миграции базы данных
- Запустит Django development server на `http://localhost:8000`

### Выполнение миграций

Миграции выполняются автоматически при запуске Docker Compose. Если нужно выполнить миграции вручную:

```bash
# Внутри контейнера
docker compose -f docker-compose-locale.yml exec web python3 manage.py migrate

# Или локально (если установлены зависимости)
cd src && python manage.py migrate
```

### Создание тестовых данных

Для заполнения базы данных тестовыми ролями, правами и пользователями выполните команду:

```bash
# Внутри контейнера
docker compose -f docker-compose-locale.yml exec web python3 manage.py create_test_data

# Или локально
cd src && python manage.py create_test_data
```

**Опции команды:**
- `--password PASSWORD` — установить пароль для тестовых пользователей (по умолчанию: `test123456`)
- `--reset` — удалить существующие тестовые данные перед созданием новых

**Пример:**
```bash
docker compose -f docker-compose-locale.yml exec web python3 manage.py create_test_data --password mypassword123 --reset
```

**Создаваемые тестовые данные:**
- **Роли:** `admin`, `user`, `moderator`
- **Права доступа:** полный набор прав для ресурса `blog.post` (create, read, update, delete, list)
- **Пользователи:**
  - `admin@test.com` — администратор с ролью `admin`
  - `user@test.com` — обычный пользователь с ролью `user`
  - `moderator@test.com` — модератор с ролью `moderator`

### Доступ к приложению

После запуска приложение будет доступно по следующим адресам:

- **API:** `http://localhost:8000/api/v1/`
- **Swagger UI:** `http://localhost:8000/api/swagger/`
- **ReDoc:** `http://localhost:8000/api/redoc/`
- **Админ-панель Django:** `http://localhost:8000/admin/`

**Примечание:** Для доступа к админ-панели необходимо создать суперпользователя:

```bash
docker compose -f docker-compose-locale.yml exec web python3 manage.py createsuperuser
```

## Структура базы данных

Система использует PostgreSQL для хранения данных. Ниже описаны все модели и их взаимосвязи.

### Схема связей

```
User (пользователь)
├── UserRole (связь пользователя с ролью)
│   └── Role (роль)
│       └── RolePermission (связь роли с правом)
│           └── Permission (право доступа)
├── UserObjectPermission (права пользователя на объект)
│   └── Permission
└── TokenBlacklist (черный список токенов)

Role (роль)
├── RolePermission (связь роли с правом)
│   └── Permission
├── UserRole (связь роли с пользователем)
│   └── User
└── RoleObjectPermission (права роли на объект)
    └── Permission
```

### Модели

#### User (Пользователь)

Базовая модель пользователя, расширяющая `AbstractUser` из Django.

**Таблица:** `users`

**Поля:**
- `id` — первичный ключ (автоматически)
- `email` — email адрес (уникальный, используется для входа)
- `first_name` — имя (макс. 150 символов)
- `last_name` — фамилия (макс. 150 символов)
- `middle_name` — отчество (макс. 150 символов, опционально)
- `password` — хеш пароля
- `is_active` — активен ли пользователь (по умолчанию: `True`)
- `is_staff` — является ли сотрудником (для доступа к админ-панели)
- `is_superuser` — является ли суперпользователем
- `deleted_at` — дата мягкого удаления (опционально, `null` если не удален)
- `date_joined` — дата регистрации (автоматически)
- `last_login` — дата последнего входа (опционально)

**Особенности:**
- Использует email вместо username для входа
- Поддерживает мягкое удаление через поле `deleted_at`
- Имеет методы для работы с ролями: `get_roles()`, `has_role()`, `add_role()`, `remove_role()`

**Связи:**
- `user_roles` → `UserRole` (многие ко многим через промежуточную таблицу)
- `user_object_permissions` → `UserObjectPermission`
- `blacklisted_tokens` → `TokenBlacklist`

#### Role (Роль)

Роль пользователя в системе. Роли могут быть системными (нельзя удалить) или пользовательскими.

**Таблица:** `roles`

**Поля:**
- `id` — первичный ключ
- `name` — название роли (уникальное, макс. 100 символов)
- `description` — описание роли (текстовое поле)
- `is_system` — системная роль (по умолчанию: `False`)
- `created_at` — дата создания (автоматически)
- `updated_at` — дата обновления (автоматически)

**Особенности:**
- Системные роли (`is_system=True`) нельзя удалить
- Имеет методы для работы с правами: `get_permissions()`, `add_permission()`, `remove_permission()`

**Связи:**
- `role_permissions` → `RolePermission` (многие ко многим через промежуточную таблицу)
- `user_roles` → `UserRole` (многие ко многим через промежуточную таблицу)
- `role_object_permissions` → `RoleObjectPermission`

#### Permission (Право доступа)

Право доступа к ресурсу с определенным действием.

**Таблица:** `permissions`

**Поля:**
- `id` — первичный ключ
- `code` — код права (уникальный, макс. 200 символов, например: `blog.post.read`)
- `name` — название права (макс. 200 символов)
- `description` — описание права (текстовое поле)
- `resource_type` — тип ресурса (макс. 100 символов, например: `blog.post`)
- `action` — действие (выбор из: `create`, `read`, `update`, `delete`, `list`)
- `created_at` — дата создания
- `updated_at` — дата обновления

**Формат кода права:**
Код права формируется как `{resource_type}.{action}`. Например:
- `blog.post.create` — создание поста
- `blog.post.read` — чтение поста
- `blog.post.update` — обновление поста
- `blog.post.delete` — удаление поста
- `blog.post.list` — список постов

**Связи:**
- `role_permissions` → `RolePermission`
- `user_object_permissions` → `UserObjectPermission`
- `role_object_permissions` → `RoleObjectPermission`

#### RolePermission (Связь роли и права)

Промежуточная таблица для связи ролей и прав доступа (многие ко многим).

**Таблица:** `role_permissions`

**Поля:**
- `id` — первичный ключ
- `role` — внешний ключ на `Role`
- `permission` — внешний ключ на `Permission`
- `created_at` — дата создания
- `updated_at` — дата обновления

**Ограничения:**
- Уникальная комбинация `(role, permission)`

#### UserRole (Связь пользователя и роли)

Промежуточная таблица для назначения ролей пользователям (многие ко многим).

**Таблица:** `user_roles`

**Поля:**
- `id` — первичный ключ
- `user` — внешний ключ на `User`
- `role` — внешний ключ на `Role`
- `assigned_by` — пользователь, который назначил роль (внешний ключ на `User`, опционально)
- `assigned_at` — дата назначения роли (автоматически)
- `created_at` — дата создания записи
- `updated_at` — дата обновления записи

**Ограничения:**
- Уникальная комбинация `(user, role)`

#### UserObjectPermission (Права пользователя на объект)

Права доступа пользователя на конкретный объект (object-level permission).

**Таблица:** `user_object_permissions`

**Поля:**
- `id` — первичный ключ
- `user` — внешний ключ на `User`
- `permission` — внешний ключ на `Permission`
- `resource_type` — тип ресурса (макс. 100 символов, например: `blog.post`)
- `resource_id` — ID объекта ресурса (положительное целое число)
- `is_granted` — предоставлено ли право (по умолчанию: `True`, `False` означает запрет)
- `granted_by` — пользователь, который предоставил право (внешний ключ на `User`, опционально)
- `granted_at` — дата предоставления права (автоматически)
- `created_at` — дата создания записи
- `updated_at` — дата обновления записи

**Ограничения:**
- Уникальная комбинация `(user, permission, resource_type, resource_id)`

**Примеры:**
- Пользователь может читать пост с ID=1: `user=user1, permission=blog.post.read, resource_type=blog.post, resource_id=1`
- Пользователю запрещено удалять пост с ID=2: `user=user1, permission=blog.post.delete, resource_type=blog.post, resource_id=2, is_granted=False`

#### RoleObjectPermission (Права роли на объект)

Права доступа роли на конкретный объект (object-level permission для роли).

**Таблица:** `role_object_permissions`

**Поля:**
- `id` — первичный ключ
- `role` — внешний ключ на `Role`
- `permission` — внешний ключ на `Permission`
- `resource_type` — тип ресурса (макс. 100 символов)
- `resource_id` — ID объекта ресурса (положительное целое число)
- `is_granted` — предоставлено ли право (по умолчанию: `True`)
- `granted_by` — пользователь, который предоставил право (внешний ключ на `User`, опционально)
- `granted_at` — дата предоставления права (автоматически)
- `created_at` — дата создания записи
- `updated_at` — дата обновления записи

**Ограничения:**
- Уникальная комбинация `(role, permission, resource_type, resource_id)`

**Примеры:**
- Роль `moderator` может обновлять пост с ID=5: `role=moderator, permission=blog.post.update, resource_type=blog.post, resource_id=5`

#### TokenBlacklist (Черный список токенов)

Хранит информацию о заблокированных JWT токенах (для logout функциональности).

**Таблица:** `token_blacklist`

**Поля:**
- `id` — первичный ключ
- `token_jti` — JWT ID токена (уникальный, макс. 255 символов, индексируется)
- `user` — внешний ключ на `User`
- `expires_at` — дата истечения токена
- `blacklisted_at` — дата добавления в черный список (автоматически)
- `created_at` — дата создания записи
- `updated_at` — дата обновления записи

**Методы класса:**
- `cleanup_expired()` — удаляет истекшие токены из черного списка
- `is_blacklisted(token_jti)` — проверяет, находится ли токен в черном списке

### Индексы

Для оптимизации запросов созданы следующие индексы:

- **User:** `email`, `is_active`, `deleted_at`
- **Role:** `name`, `is_system`
- **Permission:** `code`, `resource_type`, `action`, `(resource_type, action)`
- **RolePermission:** `(role, permission)`
- **UserRole:** `(user, role)`, `assigned_at`
- **UserObjectPermission:** `(user, resource_type, resource_id)`, `(user, is_granted)`, `(resource_type, resource_id)`, `granted_at`
- **RoleObjectPermission:** `(role, resource_type, resource_id)`, `(role, is_granted)`, `(resource_type, resource_id)`, `granted_at`
- **TokenBlacklist:** `token_jti`, `user`, `expires_at`

## Тестирование API

Ниже приведены примеры запросов для тестирования всех эндпоинтов API. Для удобства можно использовать Swagger UI (`http://localhost:8000/api/swagger/`) или любой HTTP-клиент (Postman).

### Базовый URL

Все запросы выполняются к базовому URL: `http://localhost:8000/api/v1/`

### 1. Аутентификация

#### 1.1. Регистрация пользователя

**Эндпоинт:** `POST /api/v1/accounts/auth/register/`

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/v1/accounts/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@test.com",
    "password": "password123",
    "first_name": "Тест",
    "last_name": "тестов",
    "middle_name": "тестович"
  }'
```

**Ответ (201 Created):**
```json
{
  "user": {
    "id": 1,
    "email": "newuser@test.com",
    "first_name": "Тест",
    "last_name": "тестов",
    "middle_name": "тестович"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

#### 1.2. Вход в систему

**Эндпоинт:** `POST /api/v1/accounts/auth/login/`

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/v1/accounts/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "test123456"
  }'
```

**Ответ (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "admin@test.com",
    "first_name": "Admin",
    "last_name": "User"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Важно:** Сохраните `access` токен для последующих запросов. Токен нужно передавать в заголовке `Authorization: Bearer <token>`.

#### 1.3. Обновление токена

**Эндпоинт:** `POST /api/v1/accounts/auth/refresh/`

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/v1/accounts/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

**Ответ (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 1.4. Выход из системы

**Эндпоинт:** `POST /api/v1/accounts/auth/logout/`

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/v1/accounts/auth/logout/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

**Ответ (200 OK):**
```json
{
  "message": "Вы успешно вышли из системы"
}
```

### 2. Профиль пользователя

#### 2.1. Получение профиля

**Эндпоинт:** `GET /api/v1/accounts/users/me/`

**Запрос:**
```bash
curl -X GET http://localhost:8000/api/v1/accounts/users/me/ \
  -H "Authorization: Bearer <access_token>"
```

**Ответ (200 OK):**
```json
{
  "id": 1,
  "email": "admin@test.com",
  "first_name": "Admin",
  "last_name": "User",
  "middle_name": "",
  "is_active": true,
  "date_joined": "2024-01-01T10:00:00Z"
}
```

#### 2.2. Обновление профиля

**Эндпоинт:** `PUT /api/v1/accounts/users/me/` или `PATCH /api/v1/accounts/users/me/`

**Запрос:**
```bash
curl -X PATCH http://localhost:8000/api/v1/accounts/users/me/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Новое имя",
    "last_name": "Новая фамилия"
  }'
```

#### 2.3. Мягкое удаление профиля

**Эндпоинт:** `DELETE /api/v1/accounts/users/me/`

**Запрос:**
```bash
curl -X DELETE http://localhost:8000/api/v1/accounts/users/me/ \
  -H "Authorization: Bearer <access_token>"
```

**Ответ (204 No Content)**

### 3. Проверка прав доступа

#### 3.1. Проверка нескольких прав

**Эндпоинт:** `POST /api/v1/accounts/permissions/check/`

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/v1/accounts/permissions/check/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "actions": [
      "blog.post.create",
      "blog.post.read",
      "blog.post.update",
      "blog.post.delete"
    ]
  }'
```

**Ответ (200 OK):**
```json
{
  "blog.post.create": true,
  "blog.post.read": true,
  "blog.post.update": false,
  "blog.post.delete": false
}
```

### 4. Блог (пример бизнес-логики)

#### 4.1. Получение списка постов

**Эндпоинт:** `GET /api/v1/blog/posts/`

**Требуемое право:** `blog.post.list`

**Запрос:**
```bash
curl -X GET http://localhost:8000/api/v1/blog/posts/ \
  -H "Authorization: Bearer <access_token>"
```

**Ответ (200 OK):**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "title": "Первый пост",
      "content": "Содержимое первого поста",
      "author": "admin@test.com",
      "created_at": "2024-01-01T10:00:00Z"
    },
    {
      "id": 2,
      "title": "Второй пост",
      "content": "Содержимое второго поста",
      "author": "user@test.com",
      "created_at": "2024-01-02T11:00:00Z"
    }
  ]
}
```

#### 4.2. Создание поста

**Эндпоинт:** `POST /api/v1/blog/posts/`

**Требуемое право:** `blog.post.create`

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/v1/blog/posts/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Новый пост",
    "content": "Содержимое нового поста"
  }'
```

**Ответ (201 Created):**
```json
{
  "id": 4,
  "title": "Новый пост",
  "content": "Содержимое нового поста",
  "author": "admin@test.com",
  "created_at": "2024-01-04T13:00:00Z"
}
```

#### 4.3. Получение конкретного поста

**Эндпоинт:** `GET /api/v1/blog/posts/{post_id}/`

**Требуемое право:** `blog.post.read` (для этого поста)

**Запрос:**
```bash
curl -X GET http://localhost:8000/api/v1/blog/posts/1/ \
  -H "Authorization: Bearer <access_token>"
```

**Ответ (200 OK):**
```json
{
  "id": 1,
  "title": "Первый пост",
  "content": "Содержимое первого поста",
  "author": "admin@test.com",
  "created_at": "2024-01-01T10:00:00Z"
}
```

**Если нет прав на этот пост:**
```json
{
  "message": "У вас нет прав для доступа к этому ресурсу",
  "errors": [
    {
      "code": "permission_denied",
      "detail": "Требуется право: blog.post.read для blog.post#1"
    }
  ]
}
```
**Статус:** 403 Forbidden

#### 4.4. Обновление поста

**Эндпоинт:** `PUT /api/v1/blog/posts/{post_id}/` или `PATCH /api/v1/blog/posts/{post_id}/`

**Требуемое право:** `blog.post.update` (для этого поста)

**Запрос:**
```bash
curl -X PATCH http://localhost:8000/api/v1/blog/posts/1/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Обновленный заголовок",
    "content": "Обновленное содержимое"
  }'
```

**Ответ (200 OK):**
```json
{
  "id": 1,
  "title": "Обновленный заголовок",
  "content": "Обновленное содержимое",
  "author": "admin@test.com",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-04T14:00:00Z"
}
```

#### 4.5. Удаление поста

**Эндпоинт:** `DELETE /api/v1/blog/posts/{post_id}/`

**Требуемое право:** `blog.post.delete` (для этого поста)

**Запрос:**
```bash
curl -X DELETE http://localhost:8000/api/v1/blog/posts/1/ \
  -H "Authorization: Bearer <access_token>"
```

**Ответ (204 No Content)**

### 5. Административный API (только для роли `admin`)

**Важно:** Все административные эндпоинты требуют роль `admin`. Войдите как `admin@test.com` с паролем `test123456`.

#### 5.1. Управление ролями

**Получение списка ролей:**
```bash
curl -X GET http://localhost:8000/api/v1/accounts/admin/roles/ \
  -H "Authorization: Bearer <admin_access_token>"
```

**Создание роли:**
```bash
curl -X POST http://localhost:8000/api/v1/accounts/admin/roles/ \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "editor",
    "description": "Редактор контента",
    "is_system": false
  }'
```

**Получение конкретной роли:**
```bash
curl -X GET http://localhost:8000/api/v1/accounts/admin/roles/1/ \
  -H "Authorization: Bearer <admin_access_token>"
```

**Обновление роли:**
```bash
curl -X PATCH http://localhost:8000/api/v1/accounts/admin/roles/1/ \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Обновленное описание"
  }'
```

**Удаление роли:**
```bash
curl -X DELETE http://localhost:8000/api/v1/accounts/admin/roles/1/ \
  -H "Authorization: Bearer <admin_access_token>"
```

#### 5.2. Управление правами доступа

**Получение списка прав:**
```bash
curl -X GET http://localhost:8000/api/v1/accounts/admin/permissions/ \
  -H "Authorization: Bearer <admin_access_token>"
```

**Создание права:**
```bash
curl -X POST http://localhost:8000/api/v1/accounts/admin/permissions/ \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "blog.comment.create",
    "name": "Создание комментария",
    "description": "Право на создание комментариев",
    "resource_type": "blog.comment",
    "action": "create"
  }'
```

#### 5.3. Назначение прав ролям

**Добавление права роли:**
```bash
curl -X POST http://localhost:8000/api/v1/accounts/admin/roles/1/permissions/ \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "permission_id": 1
  }'
```

**Удаление права у роли:**
```bash
curl -X DELETE http://localhost:8000/api/v1/accounts/admin/roles/1/permissions/1/ \
  -H "Authorization: Bearer <admin_access_token>"
```

#### 5.4. Назначение ролей пользователям

**Получение списка пользователей:**
```bash
curl -X GET http://localhost:8000/api/v1/accounts/admin/users/ \
  -H "Authorization: Bearer <admin_access_token>"
```

**Получение ролей пользователя:**
```bash
curl -X GET http://localhost:8000/api/v1/accounts/admin/users/1/roles/ \
  -H "Authorization: Bearer <admin_access_token>"
```

**Назначение роли пользователю:**
```bash
curl -X POST http://localhost:8000/api/v1/accounts/admin/users/1/roles/ \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "role_id": 2
  }'
```

**Удаление роли у пользователя:**
```bash
curl -X DELETE http://localhost:8000/api/v1/accounts/admin/users/1/roles/2/ \
  -H "Authorization: Bearer <admin_access_token>"
```

### Пример полного флоу тестирования

1. **Регистрация нового пользователя:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/accounts/auth/register/ \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "test123456", "first_name": "Test", "last_name": "User"}'
   ```
   Сохраните `access` токен из ответа.

2. **Вход как администратор:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/accounts/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@test.com", "password": "test123456"}'
   ```
   Сохраните `access` токен администратора.

3. **Проверка прав обычного пользователя:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/accounts/permissions/check/ \
     -H "Authorization: Bearer <user_access_token>" \
     -H "Content-Type: application/json" \
     -d '{"actions": ["blog.post.list", "blog.post.create"]}'
   ```

4. **Попытка создать пост (если есть право):**
   ```bash
   curl -X POST http://localhost:8000/api/v1/blog/posts/ \
     -H "Authorization: Bearer <user_access_token>" \
     -H "Content-Type: application/json" \
     -d '{"title": "Мой пост", "content": "Содержимое"}'
   ```

5. **Попытка прочитать пост:**
   ```bash
   curl -X GET http://localhost:8000/api/v1/blog/posts/1/ \
     -H "Authorization: Bearer <user_access_token>"
   ```

6. **Назначение роли пользователю (как администратор):**
   ```bash
   curl -X POST http://localhost:8000/api/v1/accounts/admin/users/1/roles/ \
     -H "Authorization: Bearer <admin_access_token>" \
     -H "Content-Type: application/json" \
     -d '{"role_id": 2}'
   ```

### Использование Swagger UI

Для интерактивного тестирования API используйте Swagger UI:

1. Откройте `http://localhost:8000/api/swagger/` в браузере
2. Нажмите кнопку **"Authorize"** в правом верхнем углу
3. Введите токен в формате: `Bearer <your_access_token>`
4. Теперь можно тестировать все эндпоинты прямо из браузера

### Коды ошибок

- **400 Bad Request** — неверный формат запроса или валидационные ошибки
- **401 Unauthorized** — отсутствует или неверный токен аутентификации
- **403 Forbidden** — недостаточно прав для выполнения действия
- **404 Not Found** — ресурс не найден
- **500 Internal Server Error** — внутренняя ошибка сервера
