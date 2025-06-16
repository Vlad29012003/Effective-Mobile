PROJECT_DIR = cd src
MANAGE_PY = uv run manage.py

.PHONY: migrations migrate run test migrations superuser generate_schema run_celery_worker messages compile docker_dev test_django test_domain

# Запуск сервера
run:
	${PROJECT_DIR} && ${MANAGE_PY} runserver

shell:
	${PROJECT_DIR} && ${MANAGE_PY} shell

worker:
	${PROJECT_DIR} && celery -A config worker --loglevel=info

beat:
	${PROJECT_DIR} && celery -A config beat --loglevel=info

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

# Запуск Celery worker
celery-worker:
	${PROJECT_DIR} && celery -A config worker --loglevel=info

# Запуск Celery beat
celery-beat:
    ${PROJECT_DIR} && celery -A config beat --loglevel=info

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
