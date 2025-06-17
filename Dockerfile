FROM python:3.12-slim-bookworm AS builder

RUN pip install --no-cache-dir uv --user

COPY pyproject.toml uv.lock* ./

ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN /root/.local/bin/uv sync --frozen --no-dev --no-install-project --no-install-workspace --no-cache

FROM python:3.12-slim-bookworm AS dev

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN adduser --disabled-password --gecos "" appuser

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src ./
COPY infra/scripts ./scripts

ARG STAGE=dev
COPY infra/envs/${STAGE}.env .env

COPY infra/scripts/start.sh ./start.sh
RUN chmod +x ./start.sh && chown appuser:appuser ./start.sh

COPY infra/scripts/celery/start-celery-worker.sh ./start-celery-worker.sh
RUN chmod +x ./start-celery-worker.sh && chown appuser:appuser ./start-celery-worker.sh

COPY infra/scripts/celery/start-celery-beat.sh ./start-celery-beat.sh
RUN chmod +x ./start-celery-beat.sh && chown appuser:appuser ./start-celery-beat.sh

USER appuser

EXPOSE 8000
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
