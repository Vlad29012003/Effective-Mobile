FROM python:3.12-slim-bookworm AS builder

RUN pip install --no-cache-dir uv --user

COPY pyproject.toml uv.lock* ./

ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN /root/.local/bin/uv sync --frozen --no-dev --no-install-project --no-install-workspace --no-cache

FROM python:3.12-slim-bookworm

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN adduser --disabled-password --gecos "" appuser

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src ./
COPY infra/scripts ./scripts

ARG STAGE=dev
COPY infra/envs/${STAGE}.env .env

RUN mkdir staticfiles && chown -R appuser:appuser staticfiles/
USER appuser

EXPOSE 8080
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "1", "--threads", "8", "--timeout", "60", "--max-requests", "30000", "--max-requests-jitter", "10000", "config.wsgi:application"]
