PROJECT_DIR = cd src
UV_RUN = uv run
MANAGE_PY = uv run manage.py

.PHONY: migrations migrate run test migrations superuser generate_schema messages compile docker_dev test_django test_domain

# Запуск сервера
run:
	${PROJECT_DIR} && ${MANAGE_PY} runserver

shell:
	${PROJECT_DIR} && ${MANAGE_PY} shell

# Celery commands removed - Celery dependencies cleaned

# Запуск тестов
tests:
	${PROJECT_DIR} && ${MANAGE_PY} test apps

# Запуск Django тестов
testapp:
	${PROJECT_DIR} && ${MANAGE_PY} test apps.${app}

# Создание миграций
migrations:
	${PROJECT_DIR} && ${MANAGE_PY} makemigrations

# Применение миграций
migrate:
	${PROJECT_DIR} && ${MANAGE_PY} migrate

# Сборка статических файлов
static:
	${PROJECT_DIR} && ${MANAGE_PY} collectstatic --noinput

# Создание суперпользователя
superuser:
	${PROJECT_DIR} && ${MANAGE_PY} createsuperuser

# Celery commands removed - Celery dependencies cleaned

# Создание сообщений для перевода
messages:
	${PROJECT_DIR} && ${MANAGE_PY} makemessages --all --ignore=env

# Компиляция сообщений
compile:
	${PROJECT_DIR} && ${MANAGE_PY} compilemessages --ignore=env

# Запуск Docker контейнеров для разработки
docker-local:
	docker compose -f docker-compose-locale.yml up --build

# Создание приложение django
startapp:
	$(PROJECT_DIR)/apps && mkdir $(name) && cd .. && $(MANAGE_PY) startapp $(name) apps/$(name)

# Проверка кода через линтер (только проверка, без изменений)
lint:
	${UV_RUN} ruff check && ${UV_RUN} ruff format --check

# Форматирование кода (исправляет импорты и форматирование)
format:
	${UV_RUN} ruff check --select I --fix && ${UV_RUN} ruff format

# Исправление всех ошибок линтера и форматирование кода
fix:
	${UV_RUN} ruff check --fix && ${UV_RUN} ruff format
